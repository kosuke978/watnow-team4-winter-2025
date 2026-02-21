import SwiftUI

struct ControllerView: View {
    @ObservedObject var controllerVM: ControllerViewModel
    var onDisconnect: () -> Void

    // ファミコンカラースキーム
    private let screenBg = Color(red: 30/255, green: 30/255, blue: 50/255)
    private let bodyMaroon = Color(red: 120/255, green: 20/255, blue: 20/255)
    private let bodyMaroonDark = Color(red: 90/255, green: 15/255, blue: 15/255)
    private let accentGold = Color(red: 245/255, green: 187/255, blue: 53/255)
    private let dpadBg = Color(red: 40/255, green: 40/255, blue: 40/255)
    private let dpadBorder = Color(red: 60/255, green: 60/255, blue: 60/255)
    private let buttonMaroon = Color(red: 140/255, green: 30/255, blue: 30/255)
    private let buttonMaroonDark = Color(red: 100/255, green: 20/255, blue: 20/255)

    var body: some View {
        ZStack {
            screenBg.ignoresSafeArea()

            GeometryReader { geo in
                let bodyWidth = geo.size.width - 32
                let bodyHeight = min(geo.size.height - 24, 280)

                VStack {
                    Spacer()

                    // コントローラーボディ（横向き）
                    ZStack {
                        // ボディ背景
                        RoundedRectangle(cornerRadius: 20)
                            .fill(
                                LinearGradient(
                                    colors: [bodyMaroon, bodyMaroonDark],
                                    startPoint: .top,
                                    endPoint: .bottom
                                )
                            )
                            .shadow(color: .black.opacity(0.5), radius: 12, x: 0, y: 6)

                        RoundedRectangle(cornerRadius: 20)
                            .stroke(Color.black.opacity(0.3), lineWidth: 2)

                        HStack(spacing: 0) {
                            // 左: D-padティルトエリア
                            dpadArea(size: bodyHeight - 60)
                                .frame(maxWidth: .infinity)

                            // 中央: ゴールドストライプ + ステータス + SELECT/START
                            VStack(spacing: 12) {
                                goldStripe(height: bodyHeight)

                                selectStartButtons
                            }
                            .frame(width: bodyWidth * 0.3)

                            // 右: A/Bボタン
                            abButtons(bodyHeight: bodyHeight)
                                .frame(maxWidth: .infinity)
                        }
                        .padding(.horizontal, 8)
                    }
                    .frame(width: bodyWidth, height: bodyHeight)

                    Spacer()
                }
                .frame(maxWidth: .infinity)
            }
        }
        .navigationBarHidden(true)
    }

    // MARK: - ゴールドストライプ（縦向き）

    private func goldStripe(height: CGFloat) -> some View {
        ZStack {
            RoundedRectangle(cornerRadius: 8)
                .fill(
                    LinearGradient(
                        colors: [
                            accentGold.opacity(0.9),
                            accentGold,
                            accentGold.opacity(0.9)
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )

            VStack(spacing: 6) {
                // プレイヤー番号
                Text("P\(controllerVM.currentData?.playerId ?? 1)")
                    .font(.custom("DotGothic16-Regular", size: 18))
                    .fontWeight(.bold)
                    .foregroundColor(bodyMaroonDark)

                // 接続ステータス
                HStack(spacing: 4) {
                    Circle()
                        .fill(Color.green)
                        .frame(width: 6, height: 6)
                    Text("Connected")
                        .font(.custom("DotGothic16-Regular", size: 11))
                        .foregroundColor(bodyMaroonDark)
                }

                // キャリブレーション状態
                if controllerVM.currentData?.calibrated == true {
                    HStack(spacing: 3) {
                        Image(systemName: "scope")
                            .font(.system(size: 10))
                        Text("CAL")
                            .font(.custom("DotGothic16-Regular", size: 10))
                    }
                    .foregroundColor(bodyMaroonDark.opacity(0.7))
                }
            }
            .padding(.vertical, 8)
        }
        .frame(height: height * 0.55)
    }

    // MARK: - D-padティルトエリア

    private func dpadArea(size: CGFloat) -> some View {
        let dpadSize = min(size, 180.0)

        return ZStack {
            RoundedRectangle(cornerRadius: 16)
                .fill(dpadBg)
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(dpadBorder, lineWidth: 1.5)
                )

            // 十字線
            Path { path in
                path.move(to: CGPoint(x: dpadSize / 2, y: 12))
                path.addLine(to: CGPoint(x: dpadSize / 2, y: dpadSize - 12))
                path.move(to: CGPoint(x: 12, y: dpadSize / 2))
                path.addLine(to: CGPoint(x: dpadSize - 12, y: dpadSize / 2))
            }
            .stroke(Color.white.opacity(0.12), lineWidth: 1)
            .frame(width: dpadSize, height: dpadSize)

            // 方向矢印ヒント
            VStack {
                Image(systemName: "chevron.up")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(.white.opacity(0.15))
                Spacer()
                Image(systemName: "chevron.down")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(.white.opacity(0.15))
            }
            .frame(height: dpadSize - 40)

            HStack {
                Image(systemName: "chevron.left")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(.white.opacity(0.15))
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(.white.opacity(0.15))
            }
            .frame(width: dpadSize - 40)

            // ティルトボール
            let areaRadius = dpadSize / 2 - 20
            let offset = ballOffset(areaRadius: areaRadius)

            Circle()
                .fill(
                    RadialGradient(
                        colors: [accentGold, Color(red: 200/255, green: 140/255, blue: 20/255)],
                        center: .topLeading,
                        startRadius: 0,
                        endRadius: 22
                    )
                )
                .frame(width: 28, height: 28)
                .shadow(color: accentGold.opacity(0.5), radius: 6, x: 0, y: 2)
                .offset(x: offset.x, y: offset.y)
        }
        .frame(width: dpadSize, height: dpadSize)
    }

    private func ballOffset(areaRadius: CGFloat) -> CGPoint {
        guard let data = controllerVM.currentData else {
            return .zero
        }

        let scale: CGFloat = 1.2
        let rawX = CGFloat(data.rotation.roll) * scale
        let rawY = CGFloat(data.rotation.pitch) * scale

        let clampedX = max(-1, min(1, rawX))
        let clampedY = max(-1, min(1, rawY))

        let x = clampedX * areaRadius
        let y = clampedY * areaRadius
        let dist = sqrt(x * x + y * y)
        if dist > areaRadius {
            let ratio = areaRadius / dist
            return CGPoint(x: x * ratio, y: y * ratio)
        }

        return CGPoint(x: x, y: y)
    }

    // MARK: - A/Bボタン

    private func abButtons(bodyHeight: CGFloat) -> some View {
        let buttonSize: CGFloat = 52

        return HStack(spacing: 20) {
            // Bボタン（Disconnect）
            VStack(spacing: 5) {
                Button(action: onDisconnect) {
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [buttonMaroon, buttonMaroonDark],
                                    startPoint: .top,
                                    endPoint: .bottom
                                )
                            )
                            .frame(width: buttonSize, height: buttonSize)
                            .shadow(color: .black.opacity(0.4), radius: 3, x: 0, y: 3)

                        Circle()
                            .stroke(Color.black.opacity(0.3), lineWidth: 1.5)
                            .frame(width: buttonSize, height: buttonSize)

                        Circle()
                            .stroke(
                                LinearGradient(
                                    colors: [Color.white.opacity(0.2), Color.clear],
                                    startPoint: .top,
                                    endPoint: .center
                                ),
                                lineWidth: 1
                            )
                            .frame(width: buttonSize - 4, height: buttonSize - 4)
                    }
                }

                Text("B")
                    .font(.custom("DotGothic16-Regular", size: 13))
                    .foregroundColor(accentGold.opacity(0.7))
            }
            .offset(y: 10)

            // Aボタン（Calibrate）
            VStack(spacing: 5) {
                Button(action: {
                    controllerVM.calibrate()
                }) {
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [buttonMaroon, buttonMaroonDark],
                                    startPoint: .top,
                                    endPoint: .bottom
                                )
                            )
                            .frame(width: buttonSize, height: buttonSize)
                            .shadow(color: .black.opacity(0.4), radius: 3, x: 0, y: 3)

                        Circle()
                            .stroke(Color.black.opacity(0.3), lineWidth: 1.5)
                            .frame(width: buttonSize, height: buttonSize)

                        Circle()
                            .stroke(
                                LinearGradient(
                                    colors: [Color.white.opacity(0.2), Color.clear],
                                    startPoint: .top,
                                    endPoint: .center
                                ),
                                lineWidth: 1
                            )
                            .frame(width: buttonSize - 4, height: buttonSize - 4)
                    }
                }

                Text("A")
                    .font(.custom("DotGothic16-Regular", size: 13))
                    .foregroundColor(accentGold.opacity(0.7))
            }
        }
    }

    // MARK: - SELECT / START

    private var selectStartButtons: some View {
        HStack(spacing: 16) {
            VStack(spacing: 3) {
                Text("SELECT")
                    .font(.custom("DotGothic16-Regular", size: 8))
                    .foregroundColor(accentGold.opacity(0.5))

                Capsule()
                    .fill(Color.black.opacity(0.4))
                    .overlay(
                        Capsule()
                            .stroke(Color.white.opacity(0.1), lineWidth: 0.5)
                    )
                    .frame(width: 40, height: 12)
            }

            VStack(spacing: 3) {
                Text("START")
                    .font(.custom("DotGothic16-Regular", size: 8))
                    .foregroundColor(accentGold.opacity(0.5))

                Capsule()
                    .fill(Color.black.opacity(0.4))
                    .overlay(
                        Capsule()
                            .stroke(Color.white.opacity(0.1), lineWidth: 0.5)
                    )
                    .frame(width: 40, height: 12)
            }
        }
    }
}
