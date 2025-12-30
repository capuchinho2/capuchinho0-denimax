from flask import Blueprint, render_template, jsonify, request
import pyodbc

bp_preparacao = Blueprint('preparacao', __name__)

@bp_preparacao.route('/preparacao')
def preparacao():
    return render_template('preparacao.html')

# Exemplo de endpoint de API para listar dados de preparação
@bp_preparacao.route('/api/preparacao/lista', methods=['GET'])
def api_lista_preparacao():
    # Parâmetro opcional de viagem
    viagem = request.args.get('viagem')
    try:
        conn_str = (
            "DRIVER={iSeries Access ODBC Driver};"
            "SYSTEM=FGE5006CDP;"
            "UID=CDP174176G;"
            "PWD=CDP1753;"
        )
        sql = f"""
        SELECT MAX(DANALLCDP.ONDAITM.NUMVAG) AS ONDA, DANALLCDP.ONDAITM.VIAGEM,
        DANALLCDP.ONDAITM.PALETE||'/'||DANALLCDP.ONDAITM.TOT_PALETE AS PALETE,
        (CASE DANALLCDP.ONDAITM.TYPSUP WHEN 1 THEN 'HET' ELSE 'HOM' END) AS TIPO,
        (CASE DANALLCDP.ONDADET.MIS_DONE WHEN 'Y' THEN '<img src="/static/img/checked.PNG" width="20" height="20" >' ELSE '<img src="/static/img/no-checked1.png" width="20" height="20" >' END) AS C,
        SUM(DANALLCDP.ONDAITM.PESO) AS PESO, SUM(DANALLCDP.ONDAITM.QTDLIDA) AS QTDLIDA, SUM(DANALLCDP.ONDAITM.RCAIXAS) AS RCAIXAS,
        CAST(SUM(DANALLCDP.ONDAITM.QTDLIDA) AS FLOAT) / NULLIF(CAST(SUM(DANALLCDP.ONDAITM.RCAIXAS) AS FLOAT),0) AS PERC_PREP,
        DANALLCDP.ONDADET.MIS_OPER AS CARREGADOR,
        (CASE DANALLCDP.ONDAITM.PREP WHEN '          ' THEN OPERADOR.CARDES ELSE DANALLCDP.ONDAITM.PREP END) AS PREPARADOR,
        (CASE DANALLCDP.ONDAITM.PREP WHEN '          ' THEN  OPERADOR.NOMUTI ELSE GEZPRP.NOMPRP END ) AS NOME
        FROM DANALLCDP.ONDAITM
        LEFT JOIN FGE5006CDP.GEZPRP AS GEZPRP ON GEZPRP.CODPRP= DANALLCDP.ONDAITM.PREP
        LEFT JOIN DANALLCDP.ONDADET ON
        DANALLCDP.ONDADET.VIAGEM||DANALLCDP.ONDADET.PALETE = DANALLCDP.ONDAITM.VIAGEM||DANALLCDP.ONDAITM.PALETE
        LEFT JOIN ( SELECT FGE5006CDP.APUTI.CODUTI, FGE5006CDP.APUTI.NOMUTI, FGE5006CDP.GESUPE.NUMSUP,
        FGE5006CDP.GESUPE.CARDES
        FROM FGE5006CDP.GESUPE
        LEFT JOIN FGE5006CDP.APUTI ON FGE5006CDP.APUTI.CODUTI=FGE5006CDP.GESUPE.CARDES
        WHERE SUBSTR(FGE5006CDP.GESUPE.REFLIV,5,7)='{viagem if viagem else ''}' ) AS OPERADOR
        ON OPERADOR.NUMSUP=DANALLCDP.ONDAITM.NUMSUP
        WHERE 1=1
        """
        if viagem:
            sql += f" AND DANALLCDP.ONDAITM.VIAGEM='{viagem}'"
        sql += " GROUP BY DANALLCDP.ONDADET.MIS_OPER, DANALLCDP.ONDAITM.VIAGEM, DANALLCDP.ONDAITM.PALETE, DANALLCDP.ONDAITM.TOT_PALETE,"
        sql += " DANALLCDP.ONDAITM.TYPSUP, DANALLCDP.ONDAITM.USUARIO, DANALLCDP.ONDAITM.PREP, GEZPRP.NOMPRP, DANALLCDP.ONDADET.MIS_DONE,"
        sql += " OPERADOR.CARDES, OPERADOR.NOMUTI"
        sql += " ORDER BY DANALLCDP.ONDAITM.VIAGEM, DANALLCDP.ONDAITM.PALETE ASC "

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        # Mapeamento dos campos para o formato desejado
        campos_desejados = [
            'ONDA', 'VIAGEM', 'PALETE', 'FROTA', 'TIPO', 'C', 'PESO', 'QTDLIDA', 'RCAIXAS',
            'PERC_PREP', 'CARREGADOR', 'PREPARADOR', 'NOME'
        ]
        dados = []
        for row in rows:
            registro = dict(zip(columns, row))
            # Se TIPO for HOM, sempre exibe 0% igual ao site antigo
            if registro.get('TIPO') == 'HOM':
                barra_html = (
                    '<span class="progress-bar-container">'
                    '<img src="/static/img/greem.png" height="22.5" width="0">'
                    '<img src="/static/img/gray.png" height="22.5" width="138">'
                    '</span>'
                    '<span class="progress-bar-text"> 0%</span>'
                )
            else:
                try:
                    perc = float(registro.get('PERC_PREP') or 0)
                except Exception:
                    perc = 0
                perc = max(0, min(perc, 1))
                largura_total = 138
                largura_verde = round(largura_total * perc)
                largura_cinza = largura_total - largura_verde
                barra_html = (
                    f'<span class="progress-bar-container">'
                    f'<img src="/static/img/greem.png" height="22.5" width="{largura_verde}">' 
                    f'<img src="/static/img/gray.png" height="22.5" width="{largura_cinza}">' 
                    f'</span>'
                    f'<span class="progress-bar-text"> {round(perc*100,2)}%</span>'
                )
            registro['PERC_PREP'] = barra_html
            dados.append({campo: registro.get(campo) for campo in campos_desejados})
        cursor.close()
        conn.close()
        return jsonify({"success": True, "dados": dados})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "dados": []}), 500
