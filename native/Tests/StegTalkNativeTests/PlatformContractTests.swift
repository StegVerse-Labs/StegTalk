import XCTest
@testable import StegTalkNative

final class PlatformContractTests: XCTestCase {
    func testReadyRequiresGrantedPermission() throws {
        XCTAssertThrowsError(try NativePlatformStatus(
            adapterKind: .ble,
            permission: .denied,
            state: .ready,
            observedAt: Date(),
            deviceBindingHash: "device-a",
            reason: "test"
        ))
    }

    func testAdmissibilityRequiresReadyAndGranted() throws {
        let status = try NativePlatformStatus(
            adapterKind: .ble,
            permission: .granted,
            state: .ready,
            observedAt: Date(),
            deviceBindingHash: "device-a",
            reason: "test"
        )
        XCTAssertTrue(status.transportAdmissible)
    }

    func testDualSlotStoreRejectsStaleGenerationAndSurvivesOneCorruptSlot() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = try DualSlotFileStore(directory: directory)
        try store.write(payload: Data("first".utf8), generation: 1)
        try store.write(payload: Data("second".utf8), generation: 2)
        XCTAssertThrowsError(try store.write(payload: Data("stale".utf8), generation: 2))

        let corruptSlot = directory.appendingPathComponent("recovery-slot-1.json")
        try Data("corrupt".utf8).write(to: corruptSlot)
        let restored = try store.readLatest(minimumGeneration: 1)
        XCTAssertEqual(restored.generation, 2)
        XCTAssertEqual(String(data: restored.payload, encoding: .utf8), "second")
    }

    func testDualSlotStoreFailsWhenBothSlotsCorrupt() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = try DualSlotFileStore(directory: directory)
        try store.write(payload: Data("first".utf8), generation: 1)
        try store.write(payload: Data("second".utf8), generation: 2)
        try Data("corrupt".utf8).write(to: directory.appendingPathComponent("recovery-slot-0.json"))
        try Data("corrupt".utf8).write(to: directory.appendingPathComponent("recovery-slot-1.json"))
        XCTAssertThrowsError(try store.readLatest(minimumGeneration: 0))
    }
}
