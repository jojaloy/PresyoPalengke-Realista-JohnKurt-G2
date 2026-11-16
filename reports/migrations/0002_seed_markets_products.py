from django.db import migrations

MARKETS = [
    ('Carbon Market', 'Pasil, Cebu City'),
    ('Bulacao Market', 'Bulacao, Cebu City'),
    ('Taboan Market', 'Sambag II, Cebu City'),
    ('Basak Market', 'Basak San Nicolas, Cebu City'),
    ('Pasil Fish Market', 'Pasil, Cebu City'),
    ('Mambaling Market', 'Mambaling, Cebu City'),
]

PRODUCTS = [
    ('Tomato', 'vegetables'), ('Onion (red)', 'vegetables'), ('Garlic', 'vegetables'),
    ('Cabbage', 'vegetables'), ('Eggplant', 'vegetables'),
    ('Banana (lakatan)', 'fruits'), ('Mango (ripe)', 'fruits'),
    ('Pork (liempo)', 'meat'), ('Chicken (whole)', 'meat'), ('Beef (kalitiran)', 'meat'),
    ('Bangus', 'fish'), ('Tilapia', 'fish'), ('Galunggong', 'fish'),
    ('Rice (well-milled)', 'grains'), ('Egg (medium)', 'other'),
]


def seed(apps, schema_editor):
    Market = apps.get_model('reports', 'Market')
    Product = apps.get_model('reports', 'Product')
    for name, location in MARKETS:
        Market.objects.get_or_create(name=name, defaults={'location': location})
    for name, category in PRODUCTS:
        Product.objects.get_or_create(name=name, defaults={'category': category})


def unseed(apps, schema_editor):
    apps.get_model('reports', 'Market').objects.filter(name__in=[m[0] for m in MARKETS]).delete()
    apps.get_model('reports', 'Product').objects.filter(name__in=[p[0] for p in PRODUCTS]).delete()


class Migration(migrations.Migration):
    dependencies = [('reports', '0001_initial')]
    operations = [migrations.RunPython(seed, unseed)]
