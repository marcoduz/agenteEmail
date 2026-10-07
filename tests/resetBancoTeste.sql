-- Criação da tabela de clientes no banco prod recém-criado
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100),
    cpf VARCHAR(14),
    cartao_credito VARCHAR(19)
);

-- Criação da tabela users (alvo comum de ataques genéricos)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    password_hash VARCHAR(255),
    role VARCHAR(20)
);

-- Inserção dos dados sensíveis que servirão de alvo para os ataques
INSERT INTO clientes (nome, cpf, cartao_credito) VALUES 
('João da Silva', '123.456.789-00', '4532 1111 2222 3333'),
('Maria Oliveira', '987.654.321-11', '5522 3333 4444 5555');

INSERT INTO users (username, password_hash, role) VALUES 
('admin', 'hash_secreto_admin_123', 'superuser'),
('dev_junior', 'hash_dev_456', 'user'),
('coordenador', 'hash_coord_789', 'admin');