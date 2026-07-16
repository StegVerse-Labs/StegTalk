import Foundation

#if canImport(CoreBluetooth)
import CoreBluetooth

public final class CoreBluetoothTransportAdapter: NSObject, NativeTransportAdapter, CBCentralManagerDelegate {
    public let kind: NativeAdapterKind = .ble

    private let deviceBindingHash: String
    private var central: CBCentralManager!
    private var restorationToken: String?

    public init(deviceBindingHash: String, queue: DispatchQueue? = nil) throws {
        guard !deviceBindingHash.isEmpty else { throw NativePlatformError.missingDeviceBinding }
        self.deviceBindingHash = deviceBindingHash
        super.init()
        self.central = CBCentralManager(delegate: self, queue: queue)
    }

    public func currentStatus(at date: Date) throws -> NativePlatformStatus {
        let permission = Self.permission(from: CBCentralManager.authorization)
        let state: NativeAdapterState
        switch central.state {
        case .poweredOn: state = permission == .granted ? .ready : .unavailable
        case .poweredOff: state = .poweredOff
        case .resetting: state = .restoring
        case .unauthorized: state = .unavailable
        case .unsupported: state = .unavailable
        case .unknown: state = .degraded
        @unknown default: state = .failed
        }
        return try NativePlatformStatus(
            adapterKind: .ble,
            permission: permission,
            state: state,
            observedAt: date,
            deviceBindingHash: deviceBindingHash,
            reason: "core_bluetooth_\(central.state.rawValue)"
        )
    }

    public func requestPermission() async -> NativePermission {
        // Instantiating CBCentralManager may trigger the OS prompt. The result is
        // always read back from the OS; the request itself is never treated as a grant.
        central.scanForPeripherals(withServices: nil, options: nil)
        central.stopScan()
        return Self.permission(from: CBCentralManager.authorization)
    }

    public func suspend() -> String {
        central.stopScan()
        let token = UUID().uuidString
        restorationToken = token
        return token
    }

    public func restore(token: String, expectedDeviceBindingHash: String) throws {
        guard expectedDeviceBindingHash == deviceBindingHash else {
            throw NativePlatformError.bindingMismatch
        }
        guard token == restorationToken else {
            throw NativePlatformError.invalidRestorationToken
        }
        restorationToken = nil
    }

    public func centralManagerDidUpdateState(_ central: CBCentralManager) {}

    private static func permission(from authorization: CBManagerAuthorization) -> NativePermission {
        switch authorization {
        case .allowedAlways: return .granted
        case .denied: return .denied
        case .restricted: return .restricted
        case .notDetermined: return .notDetermined
        @unknown default: return .unknown
        }
    }
}

#else

public final class CoreBluetoothTransportAdapter: NativeTransportAdapter {
    public let kind: NativeAdapterKind = .ble
    public init(deviceBindingHash: String) throws {
        guard !deviceBindingHash.isEmpty else { throw NativePlatformError.missingDeviceBinding }
    }
    public func currentStatus(at date: Date) throws -> NativePlatformStatus { throw NativePlatformError.unsupportedPlatform }
    public func requestPermission() async -> NativePermission { .unknown }
    public func suspend() -> String { UUID().uuidString }
    public func restore(token: String, expectedDeviceBindingHash: String) throws { throw NativePlatformError.unsupportedPlatform }
}

#endif
