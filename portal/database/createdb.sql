-----------------------------------------------------------------------------
-- LANGUAGE
-----------------------------------------------------------------------------

DROP TABLE language CASCADE;

CREATE TABLE language
(
    lang_id serial,
    lang_name varchar (128) NOT NULL,
    lang_iso639_2 char(2) NOT NULL,
    lang_iso639_3 char(3) NOT NULL,
    country_iso3166_2 char(2) NOT NULL,
    PRIMARY KEY (lang_id)
);


-----------------------------------------------------------------------------
-- PROJECT
-----------------------------------------------------------------------------

DROP TABLE project CASCADE;

CREATE TABLE project
(
    proj_id serial,
    proj_name varchar (256) NOT NULL,
    proj_version varchar(16),
    proj_accelerator_indicator char(1),
    PRIMARY KEY (proj_id),
    CONSTRAINT proj_name_version_unique UNIQUE (proj_name, proj_version)
);


-----------------------------------------------------------------------------
-- FILE
-----------------------------------------------------------------------------

DROP TABLE file CASCADE;

CREATE TABLE file
(
    file_id serial,
    file_name varchar (256) NOT NULL,
    proj_id integer NOT NULL,
    PRIMARY KEY (file_id),
    CONSTRAINT file_name_unique UNIQUE (file_name, proj_id),
    FOREIGN KEY (proj_id) REFERENCES project(proj_id)
);


-----------------------------------------------------------------------------
-- ORIGINAL
-----------------------------------------------------------------------------

DROP TABLE original CASCADE;

CREATE TABLE original
(
    orig_id serial,
    orig_location varchar(4096) NOT NULL,
    orig_translator_comment varchar(4096),
    orig_string_raw varchar(4096) NOT NULL,
    orig_comment varchar(4096),
    orig_accelerator char(1),
    orig_string_stripped varchar(4096) NOT NULL,
    orig_wordcount integer,
    orig_charcount integer,
    orig_date_first timestamp,
    file_id integer NOT NULL,
    PRIMARY KEY (orig_id),
    FOREIGN KEY (file_id) REFERENCES file(file_id)
);


-----------------------------------------------------------------------------
-- TRANSLATION
-----------------------------------------------------------------------------

DROP TABLE translation CASCADE;

CREATE TABLE translation
(
    trans_id serial,
    trans_string_raw varchar(4096) NOT NULL,
    trans_version varchar(64) NOT NULL,
    trans_accelerator char(1),
    trans_string_stripped varchar(4096) NOT NULL,
    trans_wordcount integer,
    trans_charcount integer,
    trans_date_first timestamp,
    orig_id integer NOT NULL,
    lang_id integer NOT NULL,    
    PRIMARY KEY (trans_id),
    FOREIGN KEY (orig_id) REFERENCES original(orig_id),
    FOREIGN KEY (lang_id) REFERENCES language(lang_id)
);
