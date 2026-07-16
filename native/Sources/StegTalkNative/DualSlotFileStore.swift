import Foundation

public final class DualSlotFileStore: NativeAtomicStore {
    private struct Envelope: Codable {
        let generation: UInt64
        let payload: Data
        let checksum: String
    }

    private let directory: URL
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()

    public init(directory: URL) throws {
        self.directory = directory
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    }

    public func write(payload: Data, generation: UInt64) throws {
        let latest = try? readLatest(minimumGeneration: 0)
        if let latest, generation <= latest.generation { throw NativePlatformError.staleGeneration }

        let envelope = Envelope(generation: generation, payload: payload, checksum: Self.checksum(payload: payload, generation: generation))
        let data = try encoder.encode(envelope)
        let slot = generation.isMultiple(of: 2) ? slotURL(0) : slotURL(1)
        let temporary = slot.appendingPathExtension("tmp")
        try data.write(to: temporary, options: .atomic)
        if FileManager.default.fileExists(atPath: slot.path) {
            try FileManager.default.removeItem(at: slot)
        }
        try FileManager.default.moveItem(at: temporary, to: slot)
    }

    public func readLatest(minimumGeneration: UInt64) throws -> (payload: Data, generation: UInt64) {
        let valid = try [0, 1].compactMap { index -> Envelope? in
            let url = slotURL(index)
            guard FileManager.default.fileExists(atPath: url.path) else { return nil }
            let data = try Data(contentsOf: url)
            guard let envelope = try? decoder.decode(Envelope.self, from: data) else { return nil }
            guard envelope.checksum == Self.checksum(payload: envelope.payload, generation: envelope.generation) else { return nil }
            return envelope
        }
        guard let newest = valid.max(by: { $0.generation < $1.generation }) else { throw NativePlatformError.corruptStore }
        guard newest.generation >= minimumGeneration else { throw NativePlatformError.staleGeneration }
        return (newest.payload, newest.generation)
    }

    private func slotURL(_ index: Int) -> URL {
        directory.appendingPathComponent("recovery-slot-\(index).json")
    }

    private static func checksum(payload: Data, generation: UInt64) -> String {
        var hash: UInt64 = 1469598103934665603
        for byte in Data("\(generation):".utf8) + payload {
            hash ^= UInt64(byte)
            hash &*= 1099511628211
        }
        return String(format: "%016llx", hash)
    }
}
