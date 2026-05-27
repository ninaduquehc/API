CREATE DATABASE IF NOT EXISTS camara_db;
USE camara_db;

CREATE TABLE IF NOT EXISTS deputados (
    id INT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    sigla_partido VARCHAR(20),
    sigla_uf VARCHAR(20),
    url_foto TEXT,
    email VARCHAR(255),
    cargo_partido VARCHAR(50)
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

CREATE TABLE IF NOT EXISTS presencas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_deputado INT NOT NULL,
    ano INT NOT NULL,
    total_eventos INT,
    presencas INT,
    faltas INT,
    percentual_presenca DECIMAL(5,2),
    percentual_faltas DECIMAL(5,2),

    UNIQUE KEY unique_dep_ano (id_deputado, ano),

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

CREATE TABLE IF NOT EXISTS discursos (
    id               INT          NOT NULL AUTO_INCREMENT,
    id_deputado      INT          NOT NULL,
    ano              YEAR         NOT NULL,
    data_hora_inicio DATETIME     NOT NULL,
    data_hora_fim    DATETIME         NULL,
    tipo_discurso    VARCHAR(100)     NULL,
    sumario          TEXT             NULL,
    keywords         TEXT             NULL,
    fase_evento      VARCHAR(200)     NULL,
    transcricao      LONGTEXT         NULL,
    uri_evento       VARCHAR(500)     NULL,
 
    PRIMARY KEY (id),
    UNIQUE  KEY uq_discurso          (id_deputado, data_hora_inicio),
    FOREIGN KEY (id_deputado) REFERENCES deputados(id) ON DELETE CASCADE,
    INDEX idx_discursos_ano          (ano),
    INDEX idx_discursos_deputado     (id_deputado),
    INDEX idx_discursos_tipo         (tipo_discurso)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS discursos_temas (
    id_discurso INT          NOT NULL,
    cod_tema    VARCHAR(20)  NOT NULL,
 
    PRIMARY KEY (id_discurso, cod_tema),
    FOREIGN KEY (id_discurso) REFERENCES discursos(id) ON DELETE CASCADE,
    FOREIGN KEY (cod_tema)    REFERENCES temas(cod)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

TRUNCATE TABLE discursos_temas;

CREATE INDEX idx_presenca_dep ON presencas(id_deputado);
CREATE INDEX idx_despesas_deputado ON despesas(id_deputado);
CREATE INDEX idx_despesas_ano ON despesas(ano);
CREATE UNIQUE INDEX idx_doc_unique ON despesas(id_documento);
CREATE INDEX idx_proposicoes_deputado ON proposicoes(id_deputado);
CREATE INDEX idx_proposicoes_ano      ON proposicoes(ano);
CREATE INDEX idx_proposicoes_tipo     ON proposicoes(sigla_tipo);

