// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "StegTalkNative",
    platforms: [
        .iOS(.v15),
        .macOS(.v13)
    ],
    products: [
        .library(name: "StegTalkNative", targets: ["StegTalkNative"])
    ],
    targets: [
        .target(name: "StegTalkNative"),
        .testTarget(name: "StegTalkNativeTests", dependencies: ["StegTalkNative"])
    ]
)
