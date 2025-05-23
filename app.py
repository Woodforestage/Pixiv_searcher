import streamlit as st

st.title("こちらはR18 比率検索WEB です")
st.write("これは簡単なWebアプリです。")

name = st.text_input("お名前を入力してください")
if name:
    st.write(f"{name}さん、ようこそ！")

st.line_chart([1, 5, 2, 6, 3])  # グラフの表示
