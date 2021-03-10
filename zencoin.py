#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 10:01:59 2021

@author: Saurabh
"""

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

#1. Building a blockchain.

class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, prev_hash = '0')
        self.nodes = set()
        
    def create_block(self, proof, prev_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'prev_hash': prev_hash,
                 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
    
    def add_transaction(self, sender, reciever, amount):
        self.transactions.append({'sender':sender,
                                  'reciever':reciever,
                                  'amount':amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, prev_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash_block(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        prev_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['prev_hash'] != self.hash_block(prev_block):
                return False
            prev_proof = prev_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - prev_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            prev_block = block
            block_index += 1
        return True
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc) 
        
    def update_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > longest_chain() and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
    
#2. Mining

##Web app
app = Flask(__name__)

#Node address on port 5000
node_address = str(uuid4()).replace('-', '')

blockchain = Blockchain()

@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash_block(previous_block)
    blockchain.add_transaction(sender = node_address, reciever = 'Saurabh', amount = 0.01)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Mining Successful',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['prev_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/is_valid', methods = ['GET'])
def is_valid():
    valid = blockchain.is_chain_valid(blockchain.chain)
    if valid:
        response = {'is valid' : valid}
    else:
        response = {'is valid' : False}
    return jsonify(response), 200

#Add new transaction to blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'reciever', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Transaction Failed! Required Information is missing'
    index = blockchain.add_transaction(json['sender'], json['reciever'], json['amount'])
    response = {'message': f'The transaction has been successfully added to block {index}'}
    return jsonify(response), 201

#3. Decentralization

#Connect new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes in None:
        return 'No node'
    for node in nodes:
        blockchain.add_node(node)
    response = {'message' : 'The nodes have been connected. There nodes are : ',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

#Consensus protocol
@app.route('/update_chain', methods = ['GET'])
def update_chain():
    updated = blockchain.update_chain()
    if updated:
        response = {'message' : 'Chain in the nodes have been updated via consensus protocol'}
    else:
        response = {'message': 'Already updated'}
    return jsonify(response), 200

#Execution
app.run(host='0.0.0.0', port='5000')