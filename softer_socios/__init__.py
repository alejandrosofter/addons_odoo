# -*- coding: utf-8 -*-

from . import controllers
from . import models


def pre_init_hook(cr):
    """
    Este hook se ejecuta antes de instalar el módulo para verificar y crear las columnas necesarias
    en res_partner si no existen
    """
    # Verificar y crear las columnas necesarias
    print("EJECUTANDO SECUENCIA DE INICIO SOCIOS!!!!!!!!!!!!!!!!!!")
    cr.execute(
        """
        DO $$
        BEGIN
            -- Verificar y crear member_number
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name = 'res_partner' AND column_name = 'member_number') THEN
                ALTER TABLE res_partner ADD COLUMN member_number varchar;
                CREATE UNIQUE INDEX IF NOT EXISTS res_partner_member_number_unique ON res_partner (member_number);
            END IF;

            -- Verificar y crear fecha_nacimiento
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name = 'res_partner' AND column_name = 'fechanacimiento') THEN
                ALTER TABLE res_partner ADD COLUMN fechanacimiento date;
            END IF;

            -- Verificar y crear tipo_socio
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name = 'res_partner' AND column_name = 'tiposocio') THEN
                ALTER TABLE res_partner ADD COLUMN tiposocio varchar;
            END IF;

            -- Verificar y crear estado
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name = 'res_partner' AND column_name = 'estado') THEN
                ALTER TABLE res_partner ADD COLUMN estado varchar DEFAULT 'activo';
            END IF;

            -- Verificar y crear fecha_alta
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name = 'res_partner' AND column_name = 'fechaalta') THEN
                ALTER TABLE res_partner ADD COLUMN fechaalta date;
            END IF;

            -- Verificar y crear fecha_baja
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name = 'res_partner' AND column_name = 'fechabaja') THEN
                ALTER TABLE res_partner ADD COLUMN fechabaja date;
            END IF;

            -- Verificar y crear es_socio
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name = 'res_partner' AND column_name = 'essocio') THEN
                ALTER TABLE res_partner ADD COLUMN essocio boolean DEFAULT false;
            END IF;
            -- Verificar y crear member_number
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name = 'res_partner' AND column_name = 'member_number') THEN
                ALTER TABLE res_partner ADD COLUMN member_number varchar;
                CREATE UNIQUE INDEX IF NOT EXISTS res_partner_member_number_unique ON res_partner (member_number);
            END IF;

            -- Verificar y crear suscripcion_id
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                         WHERE table_name = 'res_partner' AND column_name = 'suscripcion_id') THEN
                ALTER TABLE res_partner ADD COLUMN suscripcion_id integer;
            -- Agregar la restricción de clave foránea
            ALTER TABLE res_partner ADD CONSTRAINT fk_res_partner_suscripcion 
                    FOREIGN KEY (suscripcion_id) 
                    REFERENCES softer_suscripciones_suscripcion(id) 
                    ON DELETE SET NULL;
            END IF;

        END;
        $$;
    """
    )
