# -*- coding: utf-8 -*-
"""
Created on Sun Sep 25 17:24:20 2023

@author: Lester Andrés García Aquino - 1003115
"""

import datetime
import hashlib
import json
from flask import Flask, jsonify, request

# Creando el blockchain
class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_block(proof=1, previous_hash={'hash': '0', 'link': None})
        
    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash']['hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

# Creando una App Web
app = Flask(__name__)

# Creando un Blockchain
blockchain = Blockchain()

# Minando un nuevo bloque
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_block_hash = blockchain.hash(previous_block)
    
    # Verificar si hay un bloque anterior al bloque anterior
    link_to_prev_prev_block = None
    if len(blockchain.chain) > 1:
        prev_prev_block_hash = blockchain.hash(blockchain.chain[-2])
        link_to_prev_prev_block = f"http://0.0.0.0:5000/get_block_by_hash/{prev_prev_block_hash}"
    else:
        link_to_prev_prev_block = "No hay bloque anterior al bloque anterior"
    
    previous_hash = {
        'hash': previous_block_hash,
        'link': link_to_prev_prev_block  # Enlace al bloque anterior al bloque anterior usando el hash
    }
    block = blockchain.create_block(proof, previous_hash)
    response = {
        'message': 'Acabas de minar un bloque',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']['hash'],
        'link_to_previous_block': block['previous_hash']['link']
    }
    return jsonify(response), 200

# Extrayendo el blockchain completo
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/get_block_by_hash/<string:block_hash>', methods=['GET'])
def get_block_by_hash(block_hash):
    for index, block in enumerate(blockchain.chain):
        if blockchain.hash(block) == block_hash:
            # Verificar si hay un bloque anterior
            if index > 0:
                return jsonify(blockchain.chain[index - 1]), 200
            else:
                return jsonify({'message': 'Este es el primer bloque, no tiene un bloque anterior'}), 404
    return jsonify({'message': 'Block not found'}), 404

@app.route('/valid', methods=['GET'])
def valid():
    valid = blockchain.is_chain_valid(blockchain.chain)
    if valid:
        response = {'message': 'Blockchain válido'}
    else:
        response = {'message': 'Blockchain no válido'}
    return jsonify(response), 200

@app.route('/modify_block', methods=['POST'])
def modify_block():
    try:
        if not request.json:
            return jsonify({'message': 'No se proporcionó un cuerpo JSON válido'}), 400

        index = request.json.get('index')
        text = request.json.get('text')

        if not index or not text:
            return jsonify({'message': 'Faltan parámetros en el cuerpo JSON'}), 400
        
        if index < 1 or index > len(blockchain.chain):
            return jsonify({'message': 'Índice inválido'}), 400
        
        # Modifica el bloque con el índice proporcionado
        block = blockchain.chain[index - 1]
        block['timestamp'] = text  # Modificamos el campo 'timestamp' como ejemplo, puedes elegir otro campo si lo prefieres
        
        # Recalcula el hash del bloque modificado y de todos los bloques subsiguientes
        for i in range(index, len(blockchain.chain)):
            current_block = blockchain.chain[i]
            previous_block = blockchain.chain[i - 1]
            current_block['previous_hash']['hash'] = blockchain.hash(previous_block)
        
        return jsonify({'message': 'Bloque modificado exitosamente'}), 200

    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# Corriendo el APP 
app.run(host='0.0.0.0', port=5000)