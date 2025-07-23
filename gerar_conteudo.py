import os


def analisar_e_escrever_arquivos():
    """
    Percorre o diretório atual e suas subpastas em busca de arquivos
    com extensões específicas (.py, .html, .css, .js) e escreve seus
    caminhos e conteúdos em um arquivo de texto.
    """
    # Obtém o caminho do diretório onde o script está sendo executado.
    pasta_raiz = os.getcwd()

    # Define as extensões de arquivo que queremos procurar.
    extensoes_desejadas = ('.py', '.html', '.css', '.js')

    # Nome do arquivo de saída.
    arquivo_saida = 'conteudo_arquivos.txt'

    try:
        with open(arquivo_saida, 'w', encoding='utf-8') as saida:
            print(f"Analisando a partir de: {pasta_raiz}")
            print(f"Os resultados serão salvos em: {arquivo_saida}\n")

            # os.walk() gera os nomes de arquivo em uma árvore de diretórios.
            for diretorio_atual, _, arquivos in os.walk(pasta_raiz):
                for nome_arquivo in arquivos:
                    # Verifica se o arquivo possui uma das extensões desejadas.
                    if nome_arquivo.endswith(extensoes_desejadas):
                        caminho_completo = os.path.join(
                            diretorio_atual, nome_arquivo)

                        # Escreve o cabeçalho com o caminho do arquivo.
                        saida.write(f"{caminho_completo}\n\n")

                        try:
                            # Abre e lê o conteúdo do arquivo encontrado.
                            with open(caminho_completo, 'r', encoding='utf-8', errors='ignore') as entrada:
                                conteudo = entrada.read()
                                saida.write(f"{conteudo}\n")
                        except Exception as e:
                            # Caso não consiga ler o arquivo, registra um erro.
                            saida.write(
                                f"--- Erro ao ler o arquivo: {e} ---\n")

                        # Adiciona um separador para maior clareza.
                        saida.write(
                            "_____________________________________\n\n")
                        print(f"Processado: {caminho_completo}")

        print(
            f"\nAnálise concluída com sucesso! Verifique o arquivo '{arquivo_saida}'.")

    except IOError as e:
        print(f"Erro ao escrever no arquivo de saída: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")


if __name__ == '__main__':
    analisar_e_escrever_arquivos()
