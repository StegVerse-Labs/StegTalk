import Foundation

public enum NativeAdapterKind: String, Codable, Sendable {
    case ble
    case wifiPeer = "wifi_peer"
}

public enum NativePermission: String, Codable, Sendable {
    case unknown
    case notDetermined = "not_determined"
    case granted
    case denied
    case restricted
    case revoked
}

public enum NativeAdapterState: String, Codable, Sendable {
    case unavailable
    case poweredOff = "powered_off"
    case ready
    case degraded
    case failed
    case suspended
    case restoring
}

public struct NativePlatformStatus: Codable, Equatable, Sendable {
    public let adapterKind: NativeAdapterKind
    public let permission: NativePermission
    public let state: NativeAdapterState
    public let observedAt: Date
    public let deviceBindingHash: String
    public let reason: String

    public init(
        adapterKind: NativeAdapterKind,
        permission: NativePermission,
        state: NativeAdapterState,
        observedAt: Date,
        deviceBindingHash: String,
        reason: String
    ) throws {
        guard !deviceBindingHash.isEmpty else { throw NativePlatformError.missingDeviceBinding }
        if state == .ready && permission != .granted {
            throw NativePlatformError.readyWithoutPermission
        }
        self.adapterKind = adapterKind
        self.permission = permission
        self.state = state
        self.observedAt = observedAt
        self.deviceBindingHash = deviceBindingHash
        self.reason = reason
    }

    public var transportAdmissible: Bool {
        permission == .granted && (state == .ready || state == .degraded)
    }
}

public enum NativePlatformError: Error, Equatable {
    case missingDeviceBinding
    case readyWithoutPermission
    case bindingMismatch
    case permissionNotGranted
    case invalidRestorationToken
    case corruptStore
    case staleGeneration
    case unsupportedPlatform
}

public protocol NativeTransportAdapter: AnyObject {
    var kind: NativeAdapterKind { get }
    func currentStatus(at date: Date) throws -> NativePlatformStatus
    func requestPermission() async -> NativePermission
    func suspend() -> String
    func restore(token: String, expectedDeviceBindingHash: String) throws
}

public protocol NativeDeviceKeyStore {
    func currentKeyID() throws -> String
    func sign(payload: Data, keyID: String) throws -> Data
    func verify(payload: Data, signature: Data, keyID: String) throws -> Bool
}

public protocol NativeAtomicStore {
    func write(payload: Data, generation: UInt64) throws
    func readLatest(minimumGeneration: UInt64) throws -> (payload: Data, generation: UInt64)
}
