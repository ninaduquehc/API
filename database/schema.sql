CREATE DATABASE IF NOT EXISTS camara_db;

USE camara_db;

CREATE TABLE IF NOT EXISTS deputados (
    id INT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    sigla_partido VARCHAR(20),
    sigla_uf VARCHAR(10),
    url_foto TEXT,
    email VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS despesas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_deputado INT NOT NULL,
    ano INT,
    mes INT,
    tipo_despesa VARCHAR(255),
    valor DECIMAL(12,2),
    nome_fornecedor VARCHAR(255),
    cnpj_cpf_fornecedor VARCHAR(50),
    data_documento DATE,
    num_documento VARCHAR(100),
    url_documento TEXT,
    id_documento VARCHAR(100),

    FOREIGN KEY (id_deputado) REFERENCES deputados(id)
);

CREATE INDEX idx_despesas_deputado ON despesas(id_deputado);
CREATE INDEX idx_despesas_ano ON despesas(ano);
CREATE UNIQUE INDEX idx_doc_unique ON despesas(id_documento);