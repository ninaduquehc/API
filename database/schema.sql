-- database/schema.sql

-- Criação do banco
CREATE DATABASE IF NOT EXISTS camara_db;

-- Seleciona o banco
USE camara_db;

-- =========================
-- TABELA DEPUTADOS
-- =========================
CREATE TABLE deputados (
    id INT PRIMARY KEY,
    nome VARCHAR(255),
    sigla_partido VARCHAR(100),
    sigla_uf VARCHAR(10),
    url_foto TEXT,
    email VARCHAR(255)
);

-- =========================
-- TABELA DESPESAS
-- =========================
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

CREATE TABLE IF NOT EXISTS presencas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_deputado INT NOT NULL,
    ano INT NOT NULL,
    total_eventos INT,
    presencas INT,
    faltas INT,
    percentual_presenca DECIMAL(5,2),
    percentual_faltas DECIMAL(5,2),
     -- Impede duplicidade de registro para o mesmo deputado no mesmo ano
    UNIQUE KEY unique_dep_ano (id_deputado, ano),

    -- Relacionamento com a tabela de deputados
    FOREIGN KEY (id_deputado) REFERENCES deputados(id)
);

CREATE TABLE IF NOT EXISTS proposicoes (
    id              INT PRIMARY KEY,
    id_deputado     INT NOT NULL,
    sigla_tipo      VARCHAR(20),
    numero          INT,
    ano             INT,
    ementa          TEXT,
    keywords        TEXT,
    situacao        VARCHAR(255),
    url_inteiro_teor TEXT,

    FOREIGN KEY (id_deputado) REFERENCES deputados(id)
);

CREATE TABLE IF NOT EXISTS temas (
    cod  VARCHAR(20) PRIMARY KEY,
    nome VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS proposicoes_temas (
    id_proposicao INT         NOT NULL,
    cod_tema      VARCHAR(20) NOT NULL,
    PRIMARY KEY (id_proposicao, cod_tema),
    FOREIGN KEY (id_proposicao) REFERENCES proposicoes(id),
    FOREIGN KEY (cod_tema)      REFERENCES temas(cod)
);


-- =========================
-- ÍNDICES
-- =========================
CREATE INDEX idx_despesas_deputado ON despesas(id_deputado);
CREATE INDEX idx_despesas_ano ON despesas(ano);
CREATE UNIQUE INDEX idx_doc_unique ON despesas(id_documento);
CREATE INDEX idx_proposicoes_deputado ON proposicoes(id_deputado);
CREATE INDEX idx_proposicoes_ano      ON proposicoes(ano);
CREATE INDEX idx_proposicoes_tipo     ON proposicoes(sigla_tipo);




