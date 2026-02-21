import SwiftUI

struct ControllerView: View {
    @ObservedObject var controllerVM: ControllerViewModel
    var onDisconnect: () -> Void

    private let borderColor = Color(red: 100/255, green: 20/255, blue: 20/255)
    private let borderWidth: CGFloat = 18

    var body: some View {
        GeometryReader { geo in
            ZStack {
                // 外枠（マルーンボーダー）
                RoundedRectangle(cornerRadius: 16)
                    .fill(borderColor)
                    .ignoresSafeArea()

                // 内側の白エリア
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.white)
                    .padding(borderWidth)

                // コンテンツ
                VStack {
                    // 上部: プレイヤーラベル
                    playerLabel
                        .padding(.top, borderWidth + 16)

                    Spacer()

                    // 下部: 戻るボタン（左）& 決定ボタン（右）
                    HStack {
                        // 戻るボタン（yajirushi）
                        Button(action: onDisconnect) {
                            bundleImage("yajirushi")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(height: geo.size.height * 0.22)
                        }

                        Spacer()

                        // 決定ボタン（button）
                        Button(action: {
                            controllerVM.calibrate()
                        }) {
                            bundleImage("button")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(height: geo.size.height * 0.22)
                        }
                    }
                    .padding(.horizontal, borderWidth + 16)
                    .padding(.bottom, borderWidth + 12)
                }
            }
        }
        .navigationBarHidden(true)
    }

    // MARK: - Bundle からの画像読み込み

    private func bundleImage(_ name: String) -> Image {
        // folder 参照: バンドル内 Resources/ サブディレクトリを探す
        if let url = Bundle.main.url(forResource: name, withExtension: "png", subdirectory: "Resources"),
           let uiImage = UIImage(contentsOfFile: url.path) {
            return Image(uiImage: uiImage)
        }
        // フラットコピーの場合
        if let path = Bundle.main.path(forResource: name, ofType: "png"),
           let uiImage = UIImage(contentsOfFile: path) {
            return Image(uiImage: uiImage)
        }
        return Image(systemName: "questionmark.circle")
    }

    // MARK: - プレイヤーラベル

    private var playerLabel: some View {
        let playerId = controllerVM.currentData?.playerId ?? 1

        return HStack(spacing: 12) {
            // キャラアイコン（1P: men, 2P: woman）
            bundleImage(playerId == 1 ? "men" : "woman")
                .resizable()
                .interpolation(.none)
                .aspectRatio(contentMode: .fit)
                .frame(height: 40)

            Text("\(playerId)P")
                .font(.custom("DotGothic16-Regular", size: 32))
                .foregroundColor(.black)
        }
        .padding(.horizontal, 32)
        .padding(.vertical, 10)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(white: 0.93))
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(Color.black, lineWidth: 2.5)
                )
        )
    }
}
