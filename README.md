# ERAIAdv (Eternal Return AI Advisor)

## 概要
Eternal Return (エターナルリターン) のプレイをリアルタイムでサポートするAIアシスタントです。
Open-LLM-VTuberをベースに、画面認識 (OCR) と公式APIを組み合わせて、マッチ中の敵プレイヤー情報の分析やコーチングを行います。

## 機能
*   **Vision Recognition**: ロード画面やスコアボードからプレイヤー名を自動認識。
*   **Stats Analysis**: 認識した名前をもとに、公式APIから詳細な戦績を取得。
*   **AI Commentary**: ローカルLLM (Ollama) が戦況に合わせてアドバイスや応援を行います。

## 環境要件
*   Windows 10/11
*   Python 3.10+
*   NVIDIA GPU (RTX 3060以上推奨) for Local LLM
*   Ollama (別途インストールが必要)

## セットアップ
(詳細は開発が進み次第追記します)
