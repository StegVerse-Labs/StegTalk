import Foundation

#if canImport(Security) && canImport(CryptoKit)
import Security
import CryptoKit

public final class KeychainDeviceKeyStore: NativeDeviceKeyStore {
    private let service: String
    private let currentKeyAccount: String

    public init(service: String = "org.stegverse.stegtalk.transport", currentKeyAccount: String = "current-key-id") {
        self.service = service
        self.currentKeyAccount = currentKeyAccount
    }

    public func currentKeyID() throws -> String {
        if let data = try read(account: currentKeyAccount), let value = String(data: data, encoding: .utf8) {
            return value
        }
        return try rotateKey()
    }

    @discardableResult
    public func rotateKey() throws -> String {
        let keyID = UUID().uuidString
        let key = SymmetricKey(size: .bits256)
        let keyData = key.withUnsafeBytes { Data($0) }
        try write(keyData, account: keyAccount(keyID))
        try write(Data(keyID.utf8), account: currentKeyAccount)
        return keyID
    }

    public func sign(payload: Data, keyID: String) throws -> Data {
        guard let keyData = try read(account: keyAccount(keyID)) else { throw NativePlatformError.corruptStore }
        let code = HMAC<SHA256>.authenticationCode(for: payload, using: SymmetricKey(data: keyData))
        return Data(code)
    }

    public func verify(payload: Data, signature: Data, keyID: String) throws -> Bool {
        guard let keyData = try read(account: keyAccount(keyID)) else { return false }
        return HMAC<SHA256>.isValidAuthenticationCode(signature, authenticating: payload, using: SymmetricKey(data: keyData))
    }

    private func keyAccount(_ keyID: String) -> String { "key-\(keyID)" }

    private func write(_ data: Data, account: String) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account
        ]
        SecItemDelete(query as CFDictionary)
        var add = query
        add[kSecValueData as String] = data
        add[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        let status = SecItemAdd(add as CFDictionary, nil)
        guard status == errSecSuccess else { throw NativePlatformError.corruptStore }
    }

    private func read(account: String) throws -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        if status == errSecItemNotFound { return nil }
        guard status == errSecSuccess else { throw NativePlatformError.corruptStore }
        return result as? Data
    }
}

#else

public final class KeychainDeviceKeyStore: NativeDeviceKeyStore {
    public init(service: String = "org.stegverse.stegtalk.transport", currentKeyAccount: String = "current-key-id") {}
    public func currentKeyID() throws -> String { throw NativePlatformError.unsupportedPlatform }
    public func sign(payload: Data, keyID: String) throws -> Data { throw NativePlatformError.unsupportedPlatform }
    public func verify(payload: Data, signature: Data, keyID: String) throws -> Bool { throw NativePlatformError.unsupportedPlatform }
}

#endif
