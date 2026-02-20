import SwiftUI

struct ControllerView: View {
    @ObservedObject var controllerVM: ControllerViewModel
    var onDisconnect: () -> Void

    var body: some View {
        VStack(spacing: 20) {
            connectedBanner

            calibrateButton

            sensorDataDisplay

            Spacer()

            disconnectButton
        }
        .padding()
        .navigationTitle("Controller")
        .navigationBarBackButtonHidden(true)
    }

    // MARK: - Subviews

    private var connectedBanner: some View {
        HStack {
            Circle()
                .fill(Color.green)
                .frame(width: 12, height: 12)
            Text("Connected")
                .font(.subheadline)
                .foregroundColor(.green)
        }
        .padding(.vertical, 8)
    }

    private var calibrateButton: some View {
        Button(action: {
            controllerVM.calibrate()
        }) {
            Text("Calibrate")
                .font(.headline)
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.green)
                .foregroundColor(.white)
                .cornerRadius(12)
        }
    }

    private var sensorDataDisplay: some View {
        VStack(alignment: .leading, spacing: 16) {
            if let data = controllerVM.currentData {
                sensorSection(title: "Acceleration", values: [
                    ("X", data.acceleration.x, "m/s\u{00B2}"),
                    ("Y", data.acceleration.y, "m/s\u{00B2}"),
                    ("Z", data.acceleration.z, "m/s\u{00B2}")
                ])

                sensorSection(title: "Rotation", values: [
                    ("Pitch", data.rotation.pitch, "rad"),
                    ("Roll", data.rotation.roll, "rad"),
                    ("Yaw", data.rotation.yaw, "rad")
                ])
            } else {
                Text("Waiting for sensor data...")
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }

    private func sensorSection(title: String, values: [(String, Double, String)]) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.headline)

            ForEach(values, id: \.0) { label, value, unit in
                HStack {
                    Text("\(label):")
                        .font(.system(.body, design: .monospaced))
                        .frame(width: 60, alignment: .leading)
                    Text(String(format: "%+.3f", value))
                        .font(.system(.body, design: .monospaced))
                        .frame(width: 80, alignment: .trailing)
                    Text(unit)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
    }

    private var disconnectButton: some View {
        Button(action: onDisconnect) {
            Text("Disconnect")
                .font(.headline)
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.red)
                .foregroundColor(.white)
                .cornerRadius(12)
        }
    }
}
