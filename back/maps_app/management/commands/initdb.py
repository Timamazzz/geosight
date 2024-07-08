from django.core.management.base import BaseCommand

from maps_app.models import MapStyle, ScoringConfiguration, POIConfig
from users_app.models import Company, User


class Command(BaseCommand):
    help = 'Initializes the database'

    def handle(self, *args, **options):
        styles = [
            {
                'name': 'POSITRON',
                'url': 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'
            },
            {
                'name': 'DARK_MATTER',
                'url': 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'
            },
            {
                'name': 'VOYAGER',
                'url': 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json'
            },
            {
                'name': 'POSITRON_NOLABELS',
                'url': 'https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json'
            },
            {
                'name': 'DARK_MATTER_NOLABELS',
                'url': 'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json'
            },
            {
                'name': 'VOYAGER_NOLABELS',
                'url': 'https://basemaps.cartocdn.com/gl/voyager-nolabels-gl-style/style.json'
            },
        ]

        for style in styles:
            MapStyle.objects.get_or_create(name=style['name'], defaults={'url': style['url']})
            self.stdout.write(self.style.SUCCESS(f'Successfully added/ensured existence of map style: {style["name"]}'))

        company_name = 'Default Company'
        company, created = Company.objects.get_or_create(name=company_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created company: {company_name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Company already exists: {company_name}'))

        # Create admin user
        admin_email = 'admin@admin.com'
        admin_password = 'admin'
        admin_user, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                'username': 'admin',
                'role': 'admin',
                'company': company,
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'admin',
                'last_name': 'admin'
            }
        )
        if created:
            admin_user.set_password(admin_password)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {admin_email}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Admin user already exists: {admin_email}'))

        # Initialize scoring configuration
        scoring_config, created = ScoringConfiguration.objects.get_or_create(
            is_active=True,
        )

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Successfully created scoring configuration with polygon radius: {scoring_config.polygon_radius}'))
            POI_LIST = {
                'stations': {
                    'max-score': 7,
                    'max-distance': 300,
                },
                'metro': {
                    'max-score': 16,
                    'max-distance': 500,
                },
                'crossings': {
                    'max-score': 7,
                    'max-distance': 500,
                },
                'parkings': {
                    'max-score': 7,
                    'max-distance': 300,
                },
                'offices': {
                    'max-score': 21,
                    'max-distance': 1000,
                },
                'malls': {
                    'max-score': 9,
                    'max-distance': 800,
                },
                'food': {
                    'max-score': 7,
                    'max-distance': 500,
                },
                'banks': {
                    'max-score': 13,
                    'max-distance': 800,
                },
                'stadiums': {
                    'max-score': 3,
                    'max-distance': 1000,
                },
                'hotels': {
                    'max-score': 3,
                    'max-distance': 1000,
                },
                'stores': {
                    'max-score': 7,
                    'max-distance': 1000,
                },
            }
            # Create POI configurations
            for poi_name, poi_params in POI_LIST.items():
                poi_config, created = POIConfig.objects.get_or_create(
                    scoring_configuration=scoring_config,
                    name=poi_name,
                    defaults={
                        'max_score': poi_params['max-score'],
                        'max_distance': poi_params['max-distance'],
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created POI configuration: {poi_name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'POI configuration already exists: {poi_name}'))

        else:
            self.stdout.write(self.style.SUCCESS('Scoring configuration already exists and is active'))