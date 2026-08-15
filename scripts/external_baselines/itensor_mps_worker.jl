#!/usr/bin/env julia
#
# Isolated ITensorMPS worker for the third external MPS comparison leg.
#
# Reads one neutral request JSON, evolves a qubit MPS with explicit canonical
# splits, and writes one neutral result JSON.  It imports nothing from the
# repository: the Python protocol module cannot be loaded here, so this file
# re-validates the request against the same literal contract.
#
# Two conventions are load-bearing and are echoed back in the result so a
# silent disagreement cannot pass as a green comparison:
#
#   * amplitudes are little-endian with qubit 0 varying fastest, matching the
#     Aer leg. `vec(Array(contract(psi), sites...))` gives exactly that because
#     Julia stores column-major and `sites` is in register order.
#   * the reported spectra are SQUARED Schmidt coefficients (reduced-density-
#     matrix eigenvalues), which is what ITensor's Spectrum carries: a
#     maximally entangled bond reads [0.5, 0.5], not [0.707, 0.707].
#
# Every two-qubit gate is applied through an explicit orthogonalize -> contract
# -> svd -> replace cycle rather than through `apply`, because the truncation
# error at the moment of the split is the quantity this leg exists to expose;
# `apply` performs the same split internally but discards its Spectrum.
# Non-adjacent gates are routed into adjacency with SWAPs so that every split
# on the state is one of ours and is therefore measured.

using ITensorMPS
using JSON
using SHA
using Pkg

const IM = ITensorMPS

const REQUEST_SCHEMA = "error_coupling_simulator.external_itensor_mps.request.v1"
const RESULT_SCHEMA = "error_coupling_simulator.external_itensor_mps.result.v1"
const AMPLITUDE_ORDERING = "little_endian_qubit0_fastest"
const SCHMIDT_CONVENTION =
    "squared_schmidt_coefficients_reduced_density_matrix_eigenvalues"
const SOURCE_ANCHORS = ["src/mps.jl", "src/abstractmps.jl", "src/mpo.jl", "src/defaults.jl"]

# (qubit arity, parameter arity) -- must match the Python protocol exactly.
const GATE_ARITY = Dict(
    "h" => (1, 0), "x" => (1, 0), "ry" => (1, 1), "rz" => (1, 1),
    "cx" => (2, 0), "cz" => (2, 0), "swap" => (2, 0),
)

struct WorkerError <: Exception
    message::String
end
Base.showerror(io::IO, e::WorkerError) = print(io, "worker contract violation: ", e.message)

fail(message::String) = throw(WorkerError(message))

require_keys(value, expected::Vector{String}, label::String) = begin
    isa(value, AbstractDict) || fail("$label must be an object")
    actual = sort(collect(keys(value)))
    want = sort(expected)
    actual == want || fail("$label keys differ: got $actual, want $want")
end

"""Validate the request with the same rules the Python protocol enforces."""
function validate_request(request)
    require_keys(request, ["schema", "execution_id", "seed", "cutoff",
                           "max_bond_dimension", "amplitude_ordering", "circuit"], "request")
    request["schema"] == REQUEST_SCHEMA || fail("unsupported request schema")
    occursin(r"^[a-z][a-z0-9_]*$", request["execution_id"]) || fail("bad execution_id")
    seed = request["seed"]
    (isa(seed, Integer) && seed >= 0) || fail("seed must be a nonnegative integer")
    cutoff = request["cutoff"]
    (isa(cutoff, Real) && isfinite(cutoff) && cutoff >= 0) || fail("bad cutoff")
    cap = request["max_bond_dimension"]
    (cap === nothing || (isa(cap, Integer) && cap > 0)) || fail("bad max_bond_dimension")
    request["amplitude_ordering"] == AMPLITUDE_ORDERING ||
        fail("amplitude_ordering is not the pinned convention")

    circuit = request["circuit"]
    require_keys(circuit, ["id", "qubits", "operations"], "circuit")
    n = circuit["qubits"]
    (isa(n, Integer) && 1 <= n <= 24) || fail("circuit.qubits out of range")
    ops = circuit["operations"]
    (isa(ops, AbstractVector) && !isempty(ops)) || fail("circuit.operations must be nonempty")
    for (i, op_) in enumerate(ops)
        require_keys(op_, ["gate", "targets", "parameters"], "operation $i")
        gate = op_["gate"]
        haskey(GATE_ARITY, gate) || fail("operation $i uses unsupported gate $gate")
        want_targets, want_params = GATE_ARITY[gate]
        targets = op_["targets"]
        length(targets) == want_targets || fail("operation $i target arity")
        for t in targets
            (isa(t, Integer) && 0 <= t < n) || fail("operation $i target out of register")
        end
        length(unique(targets)) == length(targets) || fail("operation $i repeats a target")
        params = op_["parameters"]
        length(params) == want_params || fail("operation $i parameter arity")
        for p in params
            (isa(p, Real) && isfinite(p)) || fail("operation $i non-finite parameter")
        end
    end
    return request
end

"""One ITensor gate for a validated neutral operation, on 1-based site indices."""
function gate_tensor(gate::String, sites, targets::Vector{Int}, params::Vector{Float64})
    if gate == "h"
        return op("H", sites[targets[1]])
    elseif gate == "x"
        return op("X", sites[targets[1]])
    elseif gate == "ry"
        return op("Ry", sites[targets[1]]; θ = params[1])
    elseif gate == "rz"
        return op("Rz", sites[targets[1]]; θ = params[1])
    elseif gate == "cx"
        return op("CNOT", sites[targets[1]], sites[targets[2]])
    elseif gate == "cz"
        return op("CZ", sites[targets[1]], sites[targets[2]])
    elseif gate == "swap"
        return op("SWAP", sites[targets[1]], sites[targets[2]])
    end
    fail("unreachable gate $gate")
end

"""Apply a two-site gate on ADJACENT sites (j, j+1) through an explicit split.

Returns the split's truncation error so the caller can accumulate it per bond.
"""
function split_apply!(psi, gate, j::Int; cutoff::Float64, maxdim)
    orthogonalize!(psi, j)
    phi = psi[j] * psi[j + 1]
    phi = gate * phi
    phi = IM.noprime(phi)
    left = j == 1 ? (siteind(psi, j),) : (linkind(psi, j - 1), siteind(psi, j))
    U, S, V, spec = maxdim === nothing ?
        IM.svd(phi, left; cutoff = cutoff) :
        IM.svd(phi, left; cutoff = cutoff, maxdim = maxdim)
    psi[j] = U
    psi[j + 1] = S * V
    return Float64(IM.truncerror(spec))
end

"""Read the spectrum at every internal bond of the current state."""
function bond_spectra(psi, n::Int)
    dims = Int[]
    spectra = Vector{Vector{Float64}}()
    actual = linkdims(psi)
    for b in 1:(n - 1)
        orthogonalize!(psi, b)
        phi = psi[b] * psi[b + 1]
        left = b == 1 ? (siteind(psi, b),) : (linkind(psi, b - 1), siteind(psi, b))
        _, _, _, spec = IM.svd(phi, left; cutoff = 0.0)
        values = sort(Float64.(IM.eigs(spec)); rev = true)
        # The bond dimension is the state's own link dimension. An SVD at
        # cutoff 0 also returns numerically-zero singular values, so reporting
        # its length would name a "bond dimension" that exceeds the cap the
        # state actually respects. Report the real dimension and the leading
        # spectrum that belongs to it.
        keep = min(actual[b], length(values))
        push!(spectra, values[1:keep])
        push!(dims, keep)
    end
    return dims, spectra
end

function runtime_identity(project_root::String)
    entry = nothing
    for value in values(Pkg.dependencies())
        if value.name == "ITensorMPS"
            entry = value
            break
        end
    end
    entry === nothing && fail("ITensorMPS is not installed in the active project")
    manifest = joinpath(project_root, "Manifest.toml")
    isfile(manifest) || fail("resolved Manifest.toml missing at $manifest")
    anchors = Dict{String,String}()
    for anchor in SOURCE_ANCHORS
        path = joinpath(entry.source, anchor)
        isfile(path) || fail("installed source anchor missing: $anchor")
        anchors[anchor] = bytes2hex(sha256(read(path)))
    end
    return Dict(
        "julia_version" => string(VERSION),
        "active_project" => Base.active_project(),
        "itensormps_version" => string(entry.version),
        "itensormps_tree_hash" => string(entry.tree_hash),
        "itensormps_source_path" => entry.source,
        "manifest_sha256" => bytes2hex(sha256(read(manifest))),
        "source_anchor_sha256" => anchors,
    )
end

function main()
    input_path = output_path = nothing
    i = 1
    while i <= length(ARGS)
        if ARGS[i] == "--input"
            input_path = ARGS[i + 1]; i += 2
        elseif ARGS[i] == "--output"
            output_path = ARGS[i + 1]; i += 2
        else
            fail("unexpected argument $(ARGS[i])")
        end
    end
    (input_path === nothing || output_path === nothing) &&
        fail("usage: itensor_mps_worker.jl --input REQUEST --output RESULT")

    # The orchestrator writes the request as canonical JSON plus one trailing
    # newline, so hashing those bytes reproduces the Python side's
    # canonical_json_sha256 without reimplementing Python's JSON canonical form
    # in Julia -- which would be a silent-drift hazard, not a convenience.
    raw = read(input_path)
    body = (!isempty(raw) && raw[end] == UInt8('\n')) ? raw[1:end - 1] : raw
    request_sha256 = bytes2hex(sha256(body))
    request = validate_request(JSON.parse(String(copy(body))))

    circuit = request["circuit"]
    n = Int(circuit["qubits"])
    cutoff = Float64(request["cutoff"])
    cap = request["max_bond_dimension"] === nothing ? nothing : Int(request["max_bond_dimension"])

    sites = siteinds("Qubit", n)
    psi = MPS(sites, fill("0", n))
    truncation = zeros(Float64, max(n - 1, 0))

    for op_ in circuit["operations"]
        gate = op_["gate"]
        # neutral targets are 0-based; ITensor sites are 1-based
        targets = Int[Int(t) + 1 for t in op_["targets"]]
        params = Float64[Float64(p) for p in op_["parameters"]]
        if length(targets) == 1
            orthogonalize!(psi, targets[1])
            psi[targets[1]] = IM.noprime(gate_tensor(gate, sites, targets, params) * psi[targets[1]])
            continue
        end
        a, b = targets[1], targets[2]
        if abs(a - b) == 1
            j = min(a, b)
            g = gate_tensor(gate, sites, targets, params)
            truncation[j] += split_apply!(psi, g, j; cutoff = cutoff, maxdim = cap)
        else
            # Route into adjacency with explicit SWAPs so every split is measured.
            lo, hi = minmax(a, b)
            for j in lo:(hi - 2)
                g = op("SWAP", sites[j], sites[j + 1])
                truncation[j] += split_apply!(psi, g, j; cutoff = cutoff, maxdim = cap)
            end
            moved = a < b ? [hi - 1, hi] : [hi, hi - 1]
            g = gate_tensor(gate, sites, moved, params)
            truncation[hi - 1] += split_apply!(psi, g, hi - 1; cutoff = cutoff, maxdim = cap)
            for j in (hi - 2):-1:lo
                gs = op("SWAP", sites[j], sites[j + 1])
                truncation[j] += split_apply!(psi, gs, j; cutoff = cutoff, maxdim = cap)
            end
        end
    end

    orthogonalize!(psi, 1)
    dims, spectra = bond_spectra(psi, n)
    amplitudes = vec(Array(contract(psi), sites...))
    norm_squared = sum(abs2, amplitudes)

    result = Dict(
        "schema" => RESULT_SCHEMA,
        "request_sha256" => request_sha256,
        "execution_id" => request["execution_id"],
        "circuit_id" => circuit["id"],
        "runtime" => runtime_identity(dirname(Base.active_project())),
        "configuration" => Dict(
            "cutoff" => cutoff,
            "max_bond_dimension" => cap === nothing ? nothing : cap,
            "seed" => request["seed"],
            "amplitude_ordering" => AMPLITUDE_ORDERING,
            "orthogonalized" => true,
        ),
        "statevector" => [[real(z), imag(z)] for z in amplitudes],
        "statevector_norm_squared" => norm_squared,
        "mps" => Dict(
            "bond_dimensions" => dims,
            "schmidt_values" => spectra,
            "schmidt_convention" => SCHMIDT_CONVENTION,
            "discarded_weight" => truncation,
        ),
    )

    temporary = output_path * ".tmp"
    open(temporary, "w") do stream
        write(stream, JSON.json(result))
        write(stream, "\n")
        flush(stream)
    end
    mv(temporary, output_path; force = true)
    println("wrote $output_path")
    return 0
end

exit(main())
