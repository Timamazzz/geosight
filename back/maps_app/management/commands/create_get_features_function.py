import os
import psycopg2
from django.core.management.base import BaseCommand
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()


class Command(BaseCommand):
    help = 'Creates or replaces the get_features function in PostgreSQL'

    def handle(self, *args, **options):
        conn_params = {
            'dbname': os.getenv('DB_NAME', settings.DATABASES['default']['NAME']),
            'user': os.getenv('DB_USER', settings.DATABASES['default']['USER']),
            'password': os.getenv('DB_PASSWORD', settings.DATABASES['default']['PASSWORD']),
            'host': os.getenv('DB_HOST', settings.DATABASES['default']['HOST']),
            'port': os.getenv('DB_PORT', settings.DATABASES['default']['PORT']),
        }

        create_function = """
               CREATE OR REPLACE FUNCTION get_features(z integer, x integer, y integer, query_params json)
               RETURNS bytea AS $$
               DECLARE
                   mvt bytea;
                   map_layer integer;
               BEGIN
                   map_layer := (query_params->>'map_layer')::integer;

                   SELECT INTO mvt ST_AsMVT(tile, 'get_features', 4096, 'geometry') FROM (
                       SELECT
                           ST_AsMVTGeom(
                               ST_Transform(ST_CurveToLine(geometry), 3857),
                               ST_TileEnvelope(z, x, y),
                               4096, 64, true
                           ) AS geometry,
                           to_json(
                                'map_layer_id', map_layer_id,
                                'info', properties::json, 
                                'id', id,
                                'type', type
                            ) AS properties
                       FROM maps_app_feature
                       WHERE map_layer_id = map_layer AND
                             geometry && ST_Transform(ST_TileEnvelope(z, x, y), 4326)
                   ) AS tile WHERE geometry IS NOT NULL;

                   RETURN mvt;
               END
               $$ LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE;
               """



        try:
            conn = psycopg2.connect(**conn_params)
            with conn.cursor() as cursor:
                cursor.execute(create_function)
            conn.commit()
            self.stdout.write(self.style.SUCCESS("Function created or replaced successfully"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))
        finally:
            conn.close()
