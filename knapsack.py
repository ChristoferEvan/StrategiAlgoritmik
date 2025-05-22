from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__, template_folder='frontend')

data = pd.read_csv('mcdonaldata.csv')


data['calories'] = pd.to_numeric(data['calories'], errors='coerce')
data['protien'] = pd.to_numeric(data['protien'], errors='coerce')
data = data.dropna(subset=['calories', 'protien'])


data['protein_per_calorie'] = data['protien'] / data['calories']


categories = sorted(data['menu'].unique())

def greedy_knapsack(menu_data, calorie_limit):
    
    sorted_items = menu_data.sort_values('protein_per_calorie', ascending=False)
    
    selected_items = []
    total_calories = 0
    total_protein = 0
    
    for _, item in sorted_items.iterrows():
        if total_calories + item['calories'] <= calorie_limit:
            selected_items.append({
                'name': item['item'],
                'calories': item['calories'],
                'protein': item['protien'],
                'category': item['menu']
            })
            total_calories += item['calories']
            total_protein += item['protien']
    
    return selected_items, total_calories, total_protein

def greedy_knapsack_with_constraints(menu_data, calorie_limit, category_constraints):

    sorted_items = menu_data.sort_values('protein_per_calorie', ascending=False)
    
    selected_items = []
    total_calories = 0
    total_protein = 0
    category_counts = {cat: 0 for cat in category_constraints.keys()}
    adjustments = {}

    for category, count in category_constraints.items():
        if count > 0:
         
            category_items = menu_data[menu_data['menu'] == category].sort_values('protein_per_calorie', ascending=False)
            
            items_added = 0
            for _, item in category_items.iterrows():
                if items_added < count and total_calories + item['calories'] <= calorie_limit:
                    selected_items.append({
                        'name': item['item'],
                        'calories': item['calories'],
                        'protein': item['protien'],
                        'category': item['menu']
                    })
                    total_calories += item['calories']
                    total_protein += item['protien']
                    items_added += 1
                    category_counts[category] += 1
            
       
            if items_added < count:
                adjustments[category] = {
                    'requested': count,
                    'actual': items_added,
                    'difference': count - items_added
                }
    

    remaining_calories = calorie_limit - total_calories
    
    if remaining_calories > 0:
        
        regular_items = menu_data[menu_data['menu'] == 'regular'].sort_values('protein_per_calorie', ascending=False)
        
        for _, item in regular_items.iterrows():
            if total_calories + item['calories'] <= calorie_limit:
                selected_items.append({
                    'name': item['item'],
                    'calories': item['calories'],
                    'protein': item['protien'],
                    'category': item['menu']
                })
                total_calories += item['calories']
                total_protein += item['protien']
    
    return selected_items, total_calories, total_protein, adjustments

@app.route('/')
def home():
    return render_template('index.html', categories=categories)

@app.route('/get_combination', methods=['POST'])
def get_combination():
    try:
        calorie_limit = int(request.form['calorie_limit'])
        is_breakfast = request.form.get('is_breakfast') == 'yes'
        beverage_count = int(request.form.get('beverage_count', 0))
        dessert_count = int(request.form.get('dessert_count', 0))
        gourmet_count = int(request.form.get('gourmet_count', 0))
        mccafe_count = int(request.form.get('mccafe_count', 0))
        
       
        if calorie_limit <= 0:
            return jsonify({'error': 'Tolong input jumlah kalori yang benar.'}), 400

      
        category_constraints = {
            'beverage': beverage_count,
            'dessert': dessert_count,
            'gourmet': gourmet_count,
            'mccafe': mccafe_count
        }
        
       
        any_constraints_active = any(count > 0 for count in category_constraints.values())
        
      
        if is_breakfast:
            filtered_data = data[data['menu'].isin(['regular', 'breakfast', 'beverage', 'dessert', 'gourmet', 'mccafe'])]
        else:
            filtered_data = data[data['menu'].isin(['regular', 'beverage', 'dessert', 'gourmet', 'mccafe'])]
        
        if any_constraints_active:
          
            selected_items, total_calories, total_protein, adjustments = greedy_knapsack_with_constraints(
                filtered_data, calorie_limit, category_constraints
            )
        else:
            
            if is_breakfast:
                regular_data = filtered_data[filtered_data['menu'].isin(['regular', 'breakfast'])]
            else:
                regular_data = filtered_data[filtered_data['menu'] == 'regular']
            
            selected_items, total_calories, total_protein = greedy_knapsack(regular_data, calorie_limit)
            adjustments = None
        
        
        organized_items = {}
        for item in selected_items:
            category = item['category']
            if category not in organized_items:
                organized_items[category] = []
            organized_items[category].append(item)
        
    
        if not selected_items:
            return jsonify({'error': 'tidak ada menu yang bisa dipilih pada batas kalori .'}), 404
        
        return jsonify({
            'selected_items': selected_items,
            'organized_items': organized_items,
            'total_calories': total_calories,
            'total_protein': total_protein,
            'adjustments': adjustments if adjustments else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)