from django.core.management.base import BaseCommand
from core.models import Category, Product

class Command(BaseCommand):
    help = 'Add sample products'

    def handle(self, *args, **kwargs):
        # Create Categories
        categories = [
            {'name': 'Physics', 'slug': 'physics', 'description': 'Physics practical notebooks'},
            {'name': 'Chemistry', 'slug': 'chemistry', 'description': 'Chemistry practical notebooks'},
            {'name': 'Biology', 'slug': 'biology', 'description': 'Biology practical notebooks'},
            {'name': 'Mathematics', 'slug': 'mathematics', 'description': 'Math practical notebooks'},
            {'name': 'ICT', 'slug': 'ict', 'description': 'ICT practical notebooks'},
        ]
        
        for cat_data in categories:
            Category.objects.get_or_create(**cat_data)
        
        # Create Products
        products = [
            {
                'name': 'SSC Physics Practical Khata',
                'slug': 'ssc-physics-practical-khata',
                'category': Category.objects.get(slug='physics'),
                'level': 'SSC',
                'description': 'Professional handwriting with perfect diagrams and experiments',
                'price': 250,
                'stock': 50,
                'featured': True,
            },
            {
                'name': 'HSC Physics Practical Khata',
                'slug': 'hsc-physics-practical-khata',
                'category': Category.objects.get(slug='physics'),
                'level': 'HSC',
                'description': 'Complete HSC physics practicals with detailed calculations',
                'price': 350,
                'stock': 40,
                'featured': True,
            },
            {
                'name': 'SSC Chemistry Practical Khata',
                'slug': 'ssc-chemistry-practical-khata',
                'category': Category.objects.get(slug='chemistry'),
                'level': 'SSC',
                'description': 'All chemistry experiments with proper observations',
                'price': 250,
                'stock': 45,
                'featured': True,
            },
            {
                'name': 'HSC Chemistry Practical Khata',
                'slug': 'hsc-chemistry-practical-khata',
                'category': Category.objects.get(slug='chemistry'),
                'level': 'HSC',
                'description': 'HSC chemistry practicals with titration calculations',
                'price': 350,
                'stock': 35,
                'featured': False,
            },
            {
                'name': 'SSC Biology Practical Khata',
                'slug': 'ssc-biology-practical-khata',
                'category': Category.objects.get(slug='biology'),
                'level': 'SSC',
                'description': 'Biology practicals with clear diagrams and labels',
                'price': 250,
                'stock': 50,
                'featured': True,
            },
            {
                'name': 'HSC Biology Practical Khata',
                'slug': 'hsc-biology-practical-khata',
                'category': Category.objects.get(slug='biology'),
                'level': 'HSC',
                'description': 'Complete HSC biology experiments and observations',
                'price': 350,
                'stock': 30,
                'featured': False,
            },
        ]
        
        for prod_data in products:
            Product.objects.get_or_create(**prod_data)
        
        self.stdout.write(self.style.SUCCESS('Sample data added successfully!'))