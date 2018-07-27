#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast
import csv
import os
import logging

func_data = []

try_data = []

handler_data = []

exception_data = []

raise_data = []

reraise_data = []

user_exception_data = [] 

custom_exceptions = {}

exceptions_catalog = {}

user_exceptions = {}

def exception_definition(exception_name):
	if exception_name == '**':
		return exception_name
	elif exception_name in user_exceptions:
		return 'usr'
	elif exception_name in custom_exceptions:
		return 'sys'
	else:
		return 'lib'

def get_exception_name(node):
	if isinstance(node, ast.Name):
		return node.id
	elif isinstance(node, ast.Attribute):
		return node.attr
	elif isinstance(node, ast.Call):
		return get_exception_name(node.func)

def get_bases(node):
	bases = []
	for el in node:
		if isinstance(el, ast.Name):
			bases.append(el.id)
		elif isinstance(el, ast.Attribute):
			bases.append(el.attr)
	return bases

def save_all(folder):
	save_csv(os.path.join(folder, 'Function'), func_data)
	save_csv(os.path.join(folder, 'Try'), try_data)
	save_csv(os.path.join(folder, 'Handler'), handler_data)
	save_csv(os.path.join(folder, 'Raise'), raise_data)
	save_csv(os.path.join(folder, 'Exception'), exception_data)
	save_csv(os.path.join(folder, 'Reraise'), reraise_data)
	save_csv(os.path.join(folder, 'UserException'), user_exception_data)

def save_csv(name, data):
	with open(name+".csv", "wb") as file_name:
		writer = csv.writer(file_name, delimiter=';')
		writer.writerows(data)

def get_directories(projectFolder):
		directories = {}
		for directory, folderName, files in os.walk(projectFolder):
			if 'example' not in directory and 'test' not in directory:
				for name in files:
					if name.endswith(".py"):
						rel_path = os.path.relpath(directory, projectFolder)
						directories[os.path.join(directory, name)] = os.path.join(rel_path, name)
		return directories

def new_dict():
	return {'try': 0, 'except-block': 0, 'generic-except': 0, 'tuple-exception': 0, 'raise': 0,
			're-raise': 0, 'statements': 0}.copy()

def load_exceptions():
	with open('ExceptionsDB.csv') as file_name:
		reader = csv.DictReader(file_name)
		for row in reader:
			exceptions_catalog[row['exception_name']] = {'level': int(row['level']), 'superclass': row['prev_name']}
			custom_exceptions[row['exception_name']] = {'level': int(row['level']), 'superclass': row['prev_name']}

def load_exception_levels(classes):
	exception_level_dict = {}
	previous_dict = {'0'}
	i = 0
	while (cmp(previous_dict, exception_level_dict)):
		previous_dict = exception_level_dict.copy()
		# Iteração sobre todas as classes definidas para identificar definições de exceções
		for class_name, class_info in classes.iteritems():
			for superclass_name in class_info:
				# Verifica se a classe esta herdando de uma Exceção
				if superclass_name in exceptions_catalog:
					# Verifica se a exceção já existe no dicionário de níveis
					if class_name in exception_level_dict:
						# Existe uma superclasse com nível maior que o nivel atual da classe
						if not exceptions_catalog[superclass_name]['level'] < exception_level_dict[class_name]['level']:
							del exception_level_dict[class_name]
							exception_level_dict[class_name] = {'level': exceptions_catalog[superclass_name]['level'] + 1, 'superclass': superclass_name}
							exceptions_catalog[class_name] = {'level': exceptions_catalog[superclass_name]['level'] + 1, 'superclass': superclass_name}
					else:
						exception_level_dict[class_name] = {'level': exceptions_catalog[superclass_name]['level'] + 1, 'superclass': superclass_name}
						exceptions_catalog[class_name] = {'level': exceptions_catalog[superclass_name]['level'] + 1, 'superclass': superclass_name}

	for exception in exception_level_dict:
		userexc_row = []
		userexc_row.extend((exception, i, exception_level_dict[exception]['level'], exception_level_dict[exception]['superclass']))
		user_exception_data.append(userexc_row)
		print user_exception_data
		i+=1

def reset_lists():
	global func_data, try_data, handler_data, exception_data, raise_data, reraise_data
	
	func_data = [['rel_path', 'class_name', 'func_name','id','raise', 're-raise','try','handlers','size']]

	try_data = [['rel_path', 'class_name', 'func_name','id','size','handlers']]

	handler_data = [['rel_path', 'class_name', 'func_name','id_try','id','size','exceptions']]

	exception_data = [['rel_path', 'class_name', 'func_name','id_handler','exception_name','origin','tuple']]

	raise_data = [['rel_path', 'class_name', 'func_name','exception_name','origin']]

	reraise_data = [['rel_path', 'class_name', 'func_name','id_handler','exception_name','origin']]

	user_exception_data = [['exception_name', 'id_exception', 'exception_level', 'parent']]

class metricCalculator:

	def run(self, folder):
		global user_exceptions
		user_exceptions = {}

		directories = get_directories(folder)
		reset_lists()
		classdef_visitor = ClassVisitor()
		last_func_id = -1
		last_try_id = -1
		last_handler_id = -1
		
		# Pegar todas as definições de exceções no projeto
		for file_name in directories:
			with open(file_name, 'r') as f:
				file_str = f.read()
				try:
					root = ast.parse(file_str)
					classdef_visitor.visit(root)
				except SyntaxError:
					logging.warning('Erro de Sintaxe no arquivo {}'.format(file_name))
					continue
				except IndentationError:
					logging.warning('Erro de indentacao no arquivo {}'.format(file_name))
					continue
		
		# Calcular medidas sobre o projeto
		for full_directory, rel_path in directories.iteritems():
			with open(full_directory, 'r') as f:
				file_str = f.read()
				print full_directory
				try:
					root = ast.parse(file_str)
					file_visitor = FileVisitor(rel_path, last_func_id, last_try_id, last_handler_id)
					file_visitor.visit(root)
					last_func_id = file_visitor.func_id_number[-1]
					last_try_id = file_visitor.try_id_number[-1]
					last_handler_id = file_visitor.handler_id_number[-1]
				except SyntaxError:
					logging.warning('Erro de Sintaxe no arquivo {}'.format(full_directory))
					continue
				except IndentationError:
					logging.warning('Erro de indentacao no arquivo {}'.format(full_directory))
					continue
		
			load_exception_levels(user_exceptions)

		save_all(folder)
	
class ClassVisitor(ast.NodeVisitor):
	
	def visit_ClassDef(self, node):
		bases = get_bases(node.bases)
		user_exceptions[node.name] = bases
	

class FileVisitor(ast.NodeVisitor):


	def __init__(self, file_name, last_func_id, last_try_id, last_handler_id):
		self.file_name = file_name
		self.func_id_number = [last_func_id]
		self.classes_stack = ['**']
		self.count = [0]

		##excecao
		self.data = [new_dict()]
		self.func_name = ['**']
		self.try_id_number = [last_try_id]
		self.handler_id_number = [last_handler_id]
		self.except_flag = [0]

	def visit_ClassDef(self, node):

		self.count = [count + 1 for count in self.count]
		
		self.classes_stack.append(node.name)
		self.generic_visit(node)
		self.classes_stack.pop()

	def visit_FunctionDef(self, node):
		
		func_row = []
		self.count = [count + 1 for count in self.count]
		
		#  EMPILHANDO CONTEXTO
		self.data.append(new_dict())
		self.count.append(0)
		self.func_name.append(node.name)
		self.func_id_number.append(self.func_id_number[-1] + 1)
		self.func_id_number[0] += 1

		self.generic_visit(node)
		
		##STATEMENTS DA FUNCAO
		self.data[-1]['statements'] = self.count[-1]

	
		##CRIANDO LINHA COM OS DADOS
		func_row.extend((self.file_name, self.classes_stack[-1], node.name, self.func_id_number[-1], self.data[-1]['raise'],
						self.data[-1]['re-raise'], self.data[-1]['try'],
						self.data[-1]['except-block'], self.data[-1]['statements']))	
		#ATRIBUINDO LINHA A TABELA
		func_data.append(func_row)
		
		#  DESEMPILHANDO CONTEXTO
		self.count.pop()
		self.func_name.pop()
		self.func_id_number.pop()
		self.data.pop()
	
	def visit_TryExcept(self, node):
		
		try_row = []
		self.count = [count + 1 for count in self.count]
		#  EMPILHANDO CONTEXTO
		self.count.append(0)
		self.try_id_number.append(self.try_id_number[-1] + 1)
		self.try_id_number[0] +=1
		self.data[-1]['try'] += 1
		self.generic_visit(node)
		
		##CRIANDO LINHA
		try_row.extend((self.file_name, self.classes_stack[-1], self.func_name[-1], self.try_id_number[-1], self.count[-1], len(node.handlers)))
		#ATRIBUINDO LINHA A TABELA
		try_data.append(try_row)
		
		#  DESEMPILHANDO CONTEXTO
		self.try_id_number.pop()
		self.count.pop()

	def visit_ExceptHandler(self, node):
		
		handler_row = []
		exception_row = []
		self.count = [count + 1 for count in self.count]
		
		#  EMPILHANDO CONTEXTO
		self.except_flag.append(1)
		self.count.append(0)
		self.handler_id_number.append(self.handler_id_number[-1] + 1)
		self.handler_id_number[0] += 1
		self.data[-1]['except-block'] += 1

		number_exceptions = 0
		##VERIFICA SE NÃO É GENERIC EXCEPT
		if node.type:
			##EXCECAO UNICA
			if isinstance(node.type, ast.Name):
				#DEF PELO SISTEMA OU USUARIO
				defby = exception_definition(node.type.id)
				#CRIANDO LINHA
				exception_row.extend((self.file_name, self.classes_stack[-1], self.func_name[-1], self.handler_id_number[-1], node.type.id, defby, 0))
				number_exceptions = 1
				#ADICIONANDO LINHA A TABELA
				exception_data.append(exception_row)
			##TUPLA DE EXCECAO
			elif isinstance(node.type, ast.Tuple):
				for exception in node.type.elts:
					exception_row = []
					name = get_exception_name(exception)
					#DEF PELO SISTEMA OU USUARIO
					defby = exception_definition(name)
					#CRIANDO LINHA
					exception_row.extend((self.file_name, self.classes_stack[-1], self.func_name[-1], self.handler_id_number[-1], name, defby, 1))
					#ADICIONANDO A TABELA
					exception_data.append(exception_row)
				
				self.data[-1]['tuple-exception'] += 1
				number_exceptions = len(node.type.elts)
		else:
			self.data[-1]['generic-except'] += 1
			number_exceptions = 0


		self.generic_visit(node)
		##CRIACAO DA LINHA COM OS DADOS
		handler_row.extend((self.file_name, self.classes_stack[-1], self.func_name[-1], self.try_id_number[-1],
							self.handler_id_number[-1], self.count[-1],
							number_exceptions))
		##ATRIBUICAO DA LINHA A TABELA
		handler_data.append(handler_row)

		#  DESEMPILHANDO CONTEXTO
		self.except_flag.pop()
		self.count.pop()
		self.handler_id_number.pop()

	def visit_Raise(self, node):

		self.count = [count + 1 for count in self.count]

		if self.except_flag[-1] == 1:
			reraise_row = []
			self.data[-1]['re-raise'] += 1
			
			exception_name = get_exception_name(node.type) if node.type else '**'
			defby = exception_definition(exception_name)

			reraise_row.extend((self.file_name, self.classes_stack[-1], self.func_name[-1], self.handler_id_number[-1], exception_name, defby))
			reraise_data.append(reraise_row)
		else:
			raise_row = []
			self.data[-1]['raise'] += 1
			
			exception_name = get_exception_name(node.type) if node.type else '**'

			defby = exception_definition(exception_name)
			
			raise_row.extend((self.file_name, self.classes_stack[-1], self.func_name[-1], exception_name, defby))
			raise_data.append(raise_row)

	def visit_Assign(self, node):
		self.count = [count + 1 for count in self.count]

	def visit_AugAssign(self, node):
		self.count = [count + 1 for count in self.count]

	def visit_Print(self, node):
		self.count = [count + 1 for count in self.count]

	def visit_Assert(self, node):
		self.count = [count + 1 for count in self.count]
		
	def visit_Delete(self, node):
		self.count = [count + 1 for count in self.count]

	def visit_Pass(self, node):
		self.count = [count + 1 for count in self.count]

	def visit_Return(self, node):
		self.count = [count + 1 for count in self.count]

	def visit_Call(self, node):
		self.count = [count + 1 for count in self.count]

if __name__ == '__main__':

	import sys
	from repositories import repos

	folder = '.' if len(sys.argv) < 2 else sys.argv[1]
	load_exceptions()

	for user, repo in repos.iteritems():
		project_name = os.path.join('resultados', repo)
		for version in os.listdir(project_name):
			mc = metricCalculator()
			mc.run(os.path.join(project_name, version))
	

	
	