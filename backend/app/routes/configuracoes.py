from flask import Blueprint, render_template, jsonify
import os
from pathlib import Path

configuracoes_bp = Blueprint('configuracoes', __name__)

@configuracoes_bp.route('/configuracoes')
def configuracoes_page():
    return render_template('configuracoes.html')

@configuracoes_bp.route('/configuracoes/limpar-cache-paletes', methods=['POST'])
def limpar_cache_paletes():
    base_dir = Path(__file__).parent.parent.parent
    dir_path = base_dir / 'cache_paletes'
    total_apagados = 0
    if dir_path.exists() and dir_path.is_dir():
        for f in dir_path.iterdir():
            if f.is_file():
                f.unlink()
                total_apagados += 1
    return jsonify({'success': True, 'apagados': total_apagados, 'message': f'{total_apagados} arquivos apagados em cache_paletes.'})

@configuracoes_bp.route('/configuracoes/limpar-cash-plts', methods=['POST'])
def limpar_cash_plts():
    base_dir = Path(__file__).parent.parent.parent
    dir_path = base_dir / 'cash_plts'
    total_apagados = 0
    if dir_path.exists() and dir_path.is_dir():
        for f in dir_path.iterdir():
            if f.is_file():
                f.unlink()
                total_apagados += 1
    return jsonify({'success': True, 'apagados': total_apagados, 'message': f'{total_apagados} arquivos apagados em cash_plts.'})
