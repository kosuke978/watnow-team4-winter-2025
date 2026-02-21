import SwiftUI

struct DebugView: View {
    @ObservedObject var connectionVM: ConnectionViewModel
    @ObservedObject var controllerVM: ControllerViewModel

    var body: some View {
        List {
            Section("Connection") {
                row("State", connectionVM.connectionState.rawValue)
                row("Server", connectionVM.signalingService.isConnected ? "Connected" : "Disconnected")
                row("Server URL", Constants.Signaling.serverURL)
            }

            Section("Sensor") {
                row("Available", controllerVM.motionService.isAvailable ? "Yes" : "No")
                row("Sending", controllerVM.isSending ? "Yes" : "No")
                row("Packets Sent", "\(controllerVM.sendCount)")
            }

            if let data = controllerVM.currentData {
                Section("Acceleration (m/s\u{00B2})") {
                    row("X", String(format: "%.4f", data.acceleration.x))
                    row("Y", String(format: "%.4f", data.acceleration.y))
                    row("Z", String(format: "%.4f", data.acceleration.z))
                }

                Section("Rotation (rad)") {
                    row("Pitch", String(format: "%.4f", data.rotation.pitch))
                    row("Roll", String(format: "%.4f", data.rotation.roll))
                    row("Yaw", String(format: "%.4f", data.rotation.yaw))
                }

                Section("Meta") {
                    row("Timestamp", String(format: "%.3f", data.timestamp))
                    row("Calibrated", data.calibrated ? "Yes" : "No")
                }
            }
        }
        .navigationTitle("Debug")
    }

    private func row(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .font(.system(.body, design: .monospaced))
        }
    }
}
