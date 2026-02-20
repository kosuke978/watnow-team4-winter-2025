import SwiftUI

struct ControllerView: View {
    @ObservedObject var controllerVM: ControllerViewModel
    var onDisconnect: () -> Void

    // ボールの移動範囲（画面幅の割合）
    private let maxOffset: CGFloat = 120

    var body: some View {
        ZStack {
            // 背景グラデーション
            LinearGradient(
                colors: [Color(.systemBackground), Color(.systemGray6)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                // 上部ステータスバー
                topBar

                Spacer()

                // メインのティルトビジュアライザー
                tiltVisualizer
                    .padding(.bottom, 20)

                // キャリブレーションボタン
                calibrateButton
                    .padding(.horizontal, 40)
                    .padding(.bottom, 16)

                // 切断ボタン
                disconnectButton
                    .padding(.horizontal, 40)
                    .padding(.bottom, 30)
            }
        }
        .navigationBarHidden(true)
    }

    // MARK: - 上部ステータスバー

    private var topBar: some View {
        HStack {
            // プレイヤー番号
            Text("P\(controllerVM.currentData?.playerId ?? 1)")
                .font(.system(size: 20, weight: .bold, design: .rounded))
                .foregroundColor(.white)
                .frame(width: 44, height: 44)
                .background(
                    Circle()
                        .fill(controllerVM.currentData?.playerId == 2 ? Color.orange : Color.cyan)
                )

            Spacer()

            // 接続ステータス
            HStack(spacing: 6) {
                Circle()
                    .fill(Color.green)
                    .frame(width: 8, height: 8)
                Text("Connected")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            // キャリブレーション状態
            Image(systemName: controllerVM.currentData?.calibrated == true ? "scope" : "circle.dashed")
                .font(.title3)
                .foregroundColor(controllerVM.currentData?.calibrated == true ? .green : .secondary)
                .frame(width: 44, height: 44)
        }
        .padding(.horizontal, 20)
        .padding(.top, 8)
    }

    // MARK: - ティルトビジュアライザー

    private var tiltVisualizer: some View {
        GeometryReader { geo in
            let size = min(geo.size.width, geo.size.height) * 0.85
            let ballSize: CGFloat = size * 0.18
            let areaRadius = size / 2 - ballSize / 2

            ZStack {
                // 外枠の円
                Circle()
                    .stroke(Color(.systemGray4), lineWidth: 2)
                    .frame(width: size, height: size)

                // グリッド線（十字）
                Path { path in
                    path.move(to: CGPoint(x: size / 2, y: 0))
                    path.addLine(to: CGPoint(x: size / 2, y: size))
                    path.move(to: CGPoint(x: 0, y: size / 2))
                    path.addLine(to: CGPoint(x: size, y: size / 2))
                }
                .stroke(Color(.systemGray5), lineWidth: 1)
                .frame(width: size, height: size)

                // 内側のガイド円
                Circle()
                    .stroke(Color(.systemGray5), lineWidth: 1)
                    .frame(width: size * 0.5, height: size * 0.5)

                // ボール（傾きに応じて移動）
                let offset = ballOffset(areaRadius: areaRadius)
                Circle()
                    .fill(
                        RadialGradient(
                            colors: [.white, Color(.systemGray2)],
                            center: .topLeading,
                            startRadius: 0,
                            endRadius: ballSize
                        )
                    )
                    .frame(width: ballSize, height: ballSize)
                    .shadow(color: .black.opacity(0.3), radius: 6, x: 2, y: 4)
                    .offset(x: offset.x, y: offset.y)
            }
            .frame(width: size, height: size)
            .position(x: geo.size.width / 2, y: geo.size.height / 2)
        }
        .aspectRatio(1, contentMode: .fit)
        .padding(.horizontal, 30)
    }

    private func ballOffset(areaRadius: CGFloat) -> CGPoint {
        guard let data = controllerVM.currentData else {
            return .zero
        }

        // roll → X軸（左右）, pitch → Y軸（上下）
        let scale: CGFloat = 1.2
        let rawX = CGFloat(data.rotation.roll) * scale
        let rawY = CGFloat(data.rotation.pitch) * scale

        // -1〜1 にクランプ
        let clampedX = max(-1, min(1, rawX))
        let clampedY = max(-1, min(1, rawY))

        // 円の範囲内に収める
        let x = clampedX * areaRadius
        let y = clampedY * areaRadius
        let dist = sqrt(x * x + y * y)
        if dist > areaRadius {
            let ratio = areaRadius / dist
            return CGPoint(x: x * ratio, y: y * ratio)
        }

        return CGPoint(x: x, y: y)
    }

    // MARK: - ボタン

    private var calibrateButton: some View {
        Button(action: {
            controllerVM.calibrate()
        }) {
            HStack(spacing: 8) {
                Image(systemName: "scope")
                Text("Calibrate")
            }
            .font(.headline)
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color(.systemGray5))
            .foregroundColor(.primary)
            .cornerRadius(14)
        }
    }

    private var disconnectButton: some View {
        Button(action: onDisconnect) {
            HStack(spacing: 8) {
                Image(systemName: "xmark.circle")
                Text("Disconnect")
            }
            .font(.headline)
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color.red.opacity(0.9))
            .foregroundColor(.white)
            .cornerRadius(14)
        }
    }
}
