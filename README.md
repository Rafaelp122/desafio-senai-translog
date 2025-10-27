# desafio-senai-translog
Solução do desafio Firjan SENAI: Sistema de controle de manutenção de veículos (TransLog) feito em Python e Django 5.

# Sistema de Controle de Manutenção - TransLog Express

![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)
![Django](https://img.shields.io/badge/Framework-Django%205.x-blue?logo=django)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-green)

## 🎯 Sobre o Projeto

Este repositório é a solução de um **Desafio Prático de Programação** proposto durante o **Curso Técnico de Desenvolvimento de Sistemas da Firjan SENAI**.

O desafio simula a criação de um sistema de controle de manutenção de veículos para a empresa fictícia **TransLog Express**. O objetivo é aplicar os conceitos fundamentais do framework Django para construir uma aplicação web funcional que gerencia a frota, registra manutenções (preventivas e corretivas), acompanha a quilometragem e emite alertas de revisão.

O sistema é desenhado para ser utilizado por três perfis de usuários distintos, com diferentes níveis de permissão: Administradores, Mecânicos e Motoristas.

## 📋 Índice

- [Principais Funcionalidades](#-principais-funcionalidades)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Instalação e Configuração Local](#-instalação-e-configuração-local)
- [Estrutura de Usuários](#-estrutura-de-usuários)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Licença](#-licença)

## ✨ Principais Funcionalidades

O sistema foi desenhado para atender aos seguintes requisitos:

- **(RF001)** Autenticação de usuários (Login/Senha).
- **(RF002)** Diferenciação de perfis de acesso (Administrador, Mecânico, Motorista).
- **(RF003)** CRUD completo de Veículos (exclusivo para Administradores).
- **(RF004)** Registro de Manutenções preventivas e corretivas.
- **(RF005)** Registro de Quilometragem atual (realizado pelo Motorista).
- **(RF006)** Dashboard com alertas visuais para veículos próximos da revisão (ex: 1.000 km restantes).
- **(RF007)** Validação de unicidade de placa (nenhum veículo pode ter placa duplicada).
- **(RF008)** Histórico de manutenções por veículo.

## 🛠️ Tecnologias Utilizadas

Este projeto foi construído utilizando as seguintes tecnologias:

- **Linguagem:** Python 3.12+  
- **Framework:** Django 5.x  
- **Banco de Dados (Desenvolvimento):** SQLite 3 (padrão do Django)  
- **Autenticação:** Sistema nativo `django.contrib.auth` (com Grupos e Permissões)  
- **Front-end:** Templates HTML5 + CSS3 (renderizados pelo Django)

## 🚀 Instalação e Configuração Local

Siga os passos abaixo para executar o projeto em sua máquina local.

### 1. Clone o Repositório

```bash
git clone https://seu-repositorio-aqui/translog.git
cd translog
```

### 2. Crie e Ative um Ambiente Virtual (Venv)

```bash
# Criar o ambiente
python -m venv venv

# Ativar no Windows
.env\Scriptsctivate

# Ativar no Linux/Mac
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
# Instale a biblioteca principal
pip install django

# (Ou instale a partir do arquivo, se existir)
pip install -r requirements.txt
```

### 4. Configure o Banco de Dados (Migrations)

O Django usará o SQLite por padrão, o que é perfeito para este desafio.

```bash
# Gera os arquivos de migração (baseado nos models.py)
python manage.py makemigrations

# Executa as migrações e cria as tabelas no banco
python manage.py migrate
```

### 5. Crie um Superusuário

```bash
python manage.py createsuperuser
# Siga as instruções para definir nome, email e senha
```

### 6. Execute o Servidor

```bash
python manage.py runserver
```

### 7. Configure os Grupos de Usuários

Para o sistema funcionar, você **DEVE** criar os perfis de acesso:

1. Acesse o painel admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)  
2. Faça login com o superusuário criado.  
3. Vá para **Grupos** e crie **3 grupos** com os nomes exatos:
   - Administrador
   - Mecanico
   - Motorista  
4. Para cada grupo, atribua as permissões corretas (ex: *Mecânico deve ter a permissão core | manutencao | Can add manutencao*).

## 👥 Estrutura de Usuários

O sistema opera com **3 níveis de permissão** pré-definidos:

### Administrador

- Tem acesso total ao sistema.  
- Único que pode cadastrar/editar/excluir Veículos.  
- Pode criar usuários e definir seus perfis (via /admin).  
- Vê o Dashboard de Alertas.

### Mecânico

- Pode registrar Manutenções (preventivas e corretivas).  
- Pode visualizar a frota de veículos.  
- Vê o Dashboard de Alertas.

### Motorista

- Tem o acesso mais restrito.  
- Sua função principal é registrar a **Quilometragem atual** do veículo (RegistroKM).

## 📁 Estrutura do Projeto

```
translog/                 # Raiz do repositório
├── translog/             # Diretório de configuração do projeto Django
│   ├── __init__.py
│   ├── settings.py       # Configurações principais
│   ├── urls.py           # URLs globais do projeto
│   └── wsgi.py
├── core/                 # Nossa aplicação principal
│   ├── __init__.py
│   ├── admin.py          # Configura o que aparece no /admin
│   ├── apps.py
│   ├── forms.py          # (Opcional) Formulários personalizados
│   ├── models.py         # Onde o DER é definido (Veiculo, Manutencao)
│   ├── views.py          # Onde a lógica (CBV ou FBV) reside
│   ├── urls.py           # URLs específicas da aplicação 'core'
│   └── migrations/       # Migrações do banco de dados
├── templates/            # Onde os arquivos HTML ficam
│   └── core/
│       ├── dashboard.html
│       └── ...
├── static/               # (Opcional) Onde CSS, JS e Imagens ficam
├── manage.py             # Script de gerenciamento do Django
└── README.md             # Este arquivo
```

## 📄 Licença

Este projeto é distribuído sob a **licença MIT**.
