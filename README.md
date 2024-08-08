# EV3プログラミング クイズアプリ  
pythonを用いたev3プログラミングの学習用アプリです。  
エラー内容をフィードバックしたり、GPTを用いたヒントの提供ができます。  
また、PCカメラを使用することで学習中の集中度や眠気を数値化できます。  
  
## デモ   
- 画面の左側にプログラムのインストラクションが表示され、右側にはデフォルトのプログラムコードが表示されます。   
  
![quiz_template](https://github.com/user-attachments/assets/40c4fc50-2f29-431e-8ced-c2b1fcc17bcc)  
  
- プログラムは特定の行のみが編集可能になっています。インストラクションに合った正しいコードを書きましょう。  

![code_edit](https://github.com/user-attachments/assets/e7c5ae30-92d6-4490-96cf-08b8ce04aca1)  
  
- プログラムを埋めたら、「回答をチェック」を押します。不正解の場合はエラー内容が表示され、該当箇所がハイライトされます。  
  
![code_eval](https://github.com/user-attachments/assets/0955c5c1-bf4c-4ee9-b8c4-b0e129f803f1)  
  
- 残り時間が少なくなると、ヒントを見ることができます。
  
![hint](https://github.com/user-attachments/assets/9732464d-ccc4-4b20-b434-f8fd9e1c42e5)  
![gpt_make_advide](https://github.com/user-attachments/assets/d6e40a5f-91f9-474c-ad13-820b98e9b30c)  
  
- 全て正解すると経過時間が表示されます。
  
![clear](https://github.com/user-attachments/assets/e8518cc2-d608-4976-8385-ffeb4b0c9d64)  
  
## 集中度と眠気の測定  
クイズ中の自分の集中状態や眠気を数値化し、可視化する事ができます。  
PCのカメラを使用して顔のキーポイントを検出し、まばたきの回数や目の開き具合を元に数値化します。  
※ 顔の検出には[Mediapipe](https://github.com/google-ai-edge/mediapipe)のFaceMeshを使用しています。  
  
![eye_tracking](https://github.com/user-attachments/assets/5166167c-78ae-4936-b1af-5244533a788e)
  
### キャリブレーション  
  目のキャリブレーションを行うことで測定の精度を上げることができます。  
  動く点を目で追ってキャリブレーションを行います。10秒ほどで終了します。
    
  ![eye_calibration](https://github.com/user-attachments/assets/4df20303-a604-4bf3-958a-c15ecd50ac3c)
