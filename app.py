import math

def poisson_prob(media, k):
    return (math.exp(-media) * media**k) / math.factorial(k)

def prob_over(media, linha):

    linha_int = int(linha)

    prob = 0
    for i in range(linha_int + 1):
        prob += poisson_prob(media, i)

    return (1 - prob) * 100


def calcular_btts(lambda_home, lambda_away):

    p_home0 = math.exp(-lambda_home)
    p_away0 = math.exp(-lambda_away)

    prob = (1 - p_home0) * (1 - p_away0)

    return prob * 100


def prever_gols(h_atq, h_def, a_atq, a_def, media_liga=2.6):

    ataque_casa = h_atq / (media_liga / 2)
    defesa_casa = h_def / (media_liga / 2)

    ataque_fora = a_atq / (media_liga / 2)
    defesa_fora = a_def / (media_liga / 2)

    lambda_home = ataque_casa * defesa_fora * (media_liga / 2)
    lambda_away = ataque_fora * defesa_casa * (media_liga / 2)

    return lambda_home, lambda_away


def prever_1x2(lambda_home, lambda_away):

    max_gols = 6

    casa = 0
    empate = 0
    fora = 0

    for i in range(max_gols):
        for j in range(max_gols):

            p = poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)

            if i > j:
                casa += p
            elif i == j:
                empate += p
            else:
                fora += p

    return casa * 100, empate * 100, fora * 100


def placares_provaveis(lambda_home, lambda_away):

    resultados = {}

    for i in range(6):
        for j in range(6):

            p = poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)

            resultados[f"{i}-{j}"] = p * 100

    top = sorted(resultados.items(), key=lambda x: x[1], reverse=True)

    return top[:5]
