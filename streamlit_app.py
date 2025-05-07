import streamlit as st
import pandas as pd
from collections import defaultdict
import io

def main():
    # URL da imagem
    image_url = "https://github.com/camaraajcv/sigpp-lote/blob/main/logoSIGRH_Cabecalho.png?raw=true"

    # Exibir imagem e textos
    html_code = f'<div style="display: flex; justify-content: center;"><img src="{image_url}" alt="Imagem" style="width:32vw;"/></div>'
    st.markdown(html_code, unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 1.5em;'>DIRETORIA DE ADMINISTRAÇÃO DA AERONÁUTICA</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; font-size: 1.2em;'>SUBDIRETORIA DE PAGAMENTO DE PESSOAL</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; font-size: 1em; text-decoration: underline;'>SIGPP</h3>", unsafe_allow_html=True)

    # Instruções
    st.write("Realizando carga de lançamentos financeiros no SIGPP")
    st.markdown("<b>A Tabela Excel deverá ter 5 COLUNAS:</b>", unsafe_allow_html=True)
    st.markdown("- <b>1ª</b> - Matrícula com Vínculo (sem pontos ou dígitos)", unsafe_allow_html=True)
    st.markdown("- <b>2ª</b> - CPF (11 dígitos, sem formatação)", unsafe_allow_html=True)
    st.markdown("- <b>3ª</b> - RUBRICA (6 dígitos)", unsafe_allow_html=True)
    st.markdown("- <b>4ª</b> - VALOR ou ÍNDICE", unsafe_allow_html=True)
    st.markdown("- <b>5ª</b> - TEXTO a ser inserido no XML (um para cada linha)", unsafe_allow_html=True)

    # Upload do arquivo
    uploaded_file = st.file_uploader("Faça upload do arquivo Excel", type=["xlsx", "xls"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file, header=None)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo Excel: {e}")
            return

        if len(df.columns) == 5:
            df.columns = ['Saram_vinculo', 'CPF', 'RUBRICA', 'VALOR', 'TEXTO_XML']
            df['Saram_vinculo'] = df['Saram_vinculo'].apply(lambda x: str(int(x)).zfill(10) if pd.notnull(x) else "")
            df['CPF'] = df['CPF'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(11)
            df['RUBRICA'] = df['RUBRICA'].apply(lambda x: str(int(float(x))).zfill(6) if pd.notnull(x) else '')
        else:
            st.error("Erro: O arquivo Excel deve ter exatamente 5 colunas.")
            return

        st.write("Pré-visualização dos dados:")
        st.write(df)

        # Formulário
        st.header("Informações Adicionais")
        col1, col2 = st.columns(2)
        with col1:
            tipo_operacao = st.selectbox("Tipo de Operação", ["I - Inclusão", "A - Alteração", "E - Exclusão", "F - Finalização"])
            inicio_direito = st.text_input("Início do Direito (AAAAMM)", max_chars=6)
            fim_direito = st.text_input("Data Final do Direito (AAAAMM)", max_chars=6)
        with col2:
            num_parcelas = st.text_input("Número de Parcelas (dois dígitos)", max_chars=2)
            valor_coluna = st.selectbox("O Valor da Planilha é um:", ["Índice", "Valor"])
            documento = st.text_input("Documento (15 dígitos)", max_chars=15)

        if inicio_direito:
            if st.button("Gerar Arquivo .txt"):
                generate_txt_file(tipo_operacao, inicio_direito, fim_direito, num_parcelas, valor_coluna, documento, df)
        else:
            st.error("Por favor, preencha o campo 'Início do Direito' antes de gerar o arquivo .txt.")


def generate_txt_file(tipo_operacao, inicio_direito, fim_direito, num_parcelas, valor_coluna, documento, df):
    if fim_direito == "":
        fim_direito = " " * 6
    if num_parcelas == "":
        num_parcelas = " " * 2

    txt_content = ""
    contador_por_cpf = defaultdict(int)

    for _, row in df.iterrows():
        cpf = row['CPF']
        contador_por_cpf[cpf] += 1
        sequencial_rubrica = str(contador_por_cpf[cpf]).zfill(2)

        if valor_coluna == "Índice":
            valor_formatado = '{:.4f}'.format(row["VALOR"])
            valor_indice = valor_formatado.replace('.', '').zfill(10)
            valor_lancamento = " " * 9
        else:
            valor_lancamento = '{:09.2f}'.format(row["VALOR"]).replace('.', '').zfill(9)
            valor_indice = " " * 10

        tipo_operacao_code = tipo_operacao.split(" ")[0]
        linha_txt = (
            f"{tipo_operacao_code}1010"
            f"{inicio_direito.zfill(6)}"
            f"{fim_direito.zfill(6)}"
            f"{row['Saram_vinculo']}"
            f"{cpf}"
            f"{row['RUBRICA']}"
            f"{sequencial_rubrica}"
            f"{num_parcelas}"
            f"{valor_indice}"
            f"{valor_lancamento}"
            f"{documento.strip().ljust(15)}"
            f"{row['TEXTO_XML']}\n"
        )

        txt_content += linha_txt

    txt_file = io.StringIO()
    txt_file.write(txt_content)

    st.download_button(
        label="Clique para baixar o arquivo .txt",
        data=txt_file.getvalue(),
        file_name="dados.txt",
        mime="text/plain"
    )

    st.success("Arquivo .txt gerado e disponível para download!")


if __name__ == "__main__":
    main()
