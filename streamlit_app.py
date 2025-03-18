import streamlit as st
import pandas as pd
import random
from datetime import datetime

# Predefined Excel file path
EXCEL_FILE_PATH = r"Meals.xlsx"
st.set_page_config(page_title="Meal Planner", layout="wide")

# Function to load data from Excel
def load_data(file_path, sheet_name=0):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    return df

# Function to save data to Excel
def save_data(data, file_path, sheet_name="Sheet1"):
    # Ensure sheet_name is valid
    if not sheet_name or sheet_name.strip() == "":
        sheet_name = "Sheet1"  # Assign default sheet name

    df = pd.DataFrame(data)

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

# Function to select random recipes for a specific day
def select_random_recipes_for_day(df, day, previous_meals):
    meals_for_day = []

    for meal_type in ['Breakfast', 'Lunch', 'Dinner']:
        # Filter meals by meal type
        meals = df[df['Meal Type'].str.contains(meal_type, case=False, na=False)]
        
        # Remove meals that have been selected in the last two days
        meals = meals[~meals['Recipe Name'].isin(previous_meals)]
        
        # Select one random meal if available
        if not meals.empty:
            selected_meal = meals.sample(n=1).iloc[0]
            meals_for_day.append({
                "Day": day,
                "Meal Type": meal_type,
                "Recipe Name": selected_meal['Recipe Name'],
                "Ingredients": selected_meal['Ingredients'],
                "Recipe Link": selected_meal['Recipe Link'] if pd.notna(selected_meal['Recipe Link']) else "N/A",
                "Notes": selected_meal['Notes'] if 'Notes' in selected_meal and pd.notna(selected_meal['Notes']) else "N/A"
            })
            # Add the selected meal to the list of previous meals
            previous_meals.append(selected_meal['Recipe Name'])

    return meals_for_day

# Main function to run the Streamlit app
def main():
    st.title("Weekly Meal Planner")
    
    # Initialize session state for data
    if 'data' not in st.session_state:
        st.session_state.data = load_data(EXCEL_FILE_PATH)
    
    # Initialize session state for menu
    if 'all_meals_for_week' not in st.session_state:
        try:
            # Load the saved menu from the Excel sheet
            st.session_state.all_meals_for_week = load_data(EXCEL_FILE_PATH, sheet_name='Weekly Menu').to_dict('records')
        except Exception as e:
            # Generate a random menu if the saved menu is not available
            previous_meals = []
            st.session_state.all_meals_for_week = []
            days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for day in days_of_week:
                meals_for_day = select_random_recipes_for_day(st.session_state.data, day, previous_meals)
                st.session_state.all_meals_for_week.extend(meals_for_day)
                if len(previous_meals) > 6:
                    previous_meals = previous_meals[-6:]

    # Sidebar for navigation
    sidebar_option = st.sidebar.selectbox("Select a section", ["Menus", "Recipes"])
    
    if sidebar_option == "Menus":
        # Generate Menu Button
        if st.button("Generate Menu"):
            
            # Initialize a list to keep track of previous meals
            previous_meals = []

            # List to store all meals for the week
            st.session_state.all_meals_for_week = []

            # Select random recipes for each day of the week
            days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for day in days_of_week:
                meals_for_day = select_random_recipes_for_day(st.session_state.data, day, previous_meals)
                st.session_state.all_meals_for_week.extend(meals_for_day)

                # Keep only the last two days of meals in the previous_meals list
                if len(previous_meals) > 6:
                    previous_meals = previous_meals[-6:]

            # Save the generated menu to the Excel file
            weekly_menu_df = pd.DataFrame(st.session_state.all_meals_for_week)
            save_data(weekly_menu_df, EXCEL_FILE_PATH, sheet_name='Weekly Menu')
            st.session_state.all_meals_for_week = load_data(EXCEL_FILE_PATH, sheet_name='Weekly Menu').to_dict('records')
            st.success("Menu generated and saved successfully!")
                
        with st.expander("View Meal"):
            # Display the weekly menu
            days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            today_index = datetime.now().weekday()
            tomorrow_index = (today_index + 1) % 7
            
            # Options to view today's, tomorrow's, or the entire week's recipes
            option = st.selectbox("Select an option", ["View Today's Recipe", "View Tomorrow's Recipe", "View Week's Recipe"])
            
            if option == "View Today's Recipe":
                st.subheader(f"Recipes for {days_of_week[today_index]}")
                today_meals = [meal for meal in st.session_state.all_meals_for_week if meal['Day'] == days_of_week[today_index]]
                today_df = pd.DataFrame(today_meals).drop(columns=['Day'])
                today_df = today_df[['Meal Type', 'Recipe Name', 'Ingredients', 'Recipe Link', 'Notes']]
                today_df['Recipe Link'] = today_df['Recipe Link'].apply(lambda x: f'<a href="{x}" target="_blank">View Recipe</a>' if x != "N/A" else "N/A")
                st.write(today_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            elif option == "View Tomorrow's Recipe":
                st.subheader(f"Recipes for {days_of_week[tomorrow_index]}")
                tomorrow_meals = [meal for meal in st.session_state.all_meals_for_week if meal['Day'] == days_of_week[tomorrow_index]]
                tomorrow_df = pd.DataFrame(tomorrow_meals).drop(columns=['Day'])
                tomorrow_df = tomorrow_df[['Meal Type', 'Recipe Name', 'Ingredients', 'Recipe Link', 'Notes']]
                tomorrow_df['Recipe Link'] = tomorrow_df['Recipe Link'].apply(lambda x: f'<a href="{x}" target="_blank">View Recipe</a>' if x != "N/A" else "N/A")
                st.write(tomorrow_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            elif option == "View Week's Recipe":
                for day in days_of_week:
                    st.subheader(f"Recipes for {day}")
                    day_meals = [meal for meal in st.session_state.all_meals_for_week if meal['Day'] == day]
                    day_df = pd.DataFrame(day_meals).drop(columns=['Day'])
                    day_df = day_df[['Meal Type', 'Recipe Name', 'Ingredients', 'Recipe Link', 'Notes']]
                    day_df['Recipe Link'] = day_df['Recipe Link'].apply(lambda x: f'<a href="{x}" target="_blank">View Recipe</a>' if x != "N/A" else "N/A")
                    st.write(day_df.to_html(escape=False, index=False), unsafe_allow_html=True)


        # Edit Meal Expander
        with st.expander("Edit Meal"):
            # Select a day to edit
            day_to_edit = st.selectbox("Select a Day to Edit", days_of_week, key="edit_day_select")

            # Select a meal type to edit
            meal_type_to_edit = st.selectbox("Select a Meal Type", ['Breakfast', 'Lunch', 'Dinner'], key="edit_meal_type_select")

            # Find the current meal for the selected day and meal type
            current_meal = next((meal for meal in st.session_state.all_meals_for_week if meal['Day'] == day_to_edit and meal['Meal Type'] == meal_type_to_edit), None)

            # Get all recipe names from the first sheet
            all_recipes = st.session_state.data['Recipe Name'].tolist()

            # Pre-select the current recipe if it exists
            selected_recipe_name = current_meal['Recipe Name'] if current_meal else all_recipes[0]

            # Select a recipe from the first sheet
            selected_recipe_name = st.selectbox("Select a Recipe", all_recipes, index=all_recipes.index(selected_recipe_name), key="select_recipe_name")

            # Find the selected recipe details
            selected_recipe = st.session_state.data[st.session_state.data['Recipe Name'] == selected_recipe_name].iloc[0]

            # Display selected recipe details
            st.write("**Selected Recipe Details:**")
            st.write(f"**Ingredients:** {selected_recipe['Ingredients']}")
            st.write(f"**Recipe Link:** {selected_recipe['Recipe Link']}")
            st.write(f"**Notes:** {selected_recipe['Notes']}")

            # Save changes button
            if st.button("Update Menu", key="update_menu_button"):
                # Update the meal in the session state
                for meal in st.session_state.all_meals_for_week:
                    if meal['Day'] == day_to_edit and meal['Meal Type'] == meal_type_to_edit:
                        meal['Recipe Name'] = selected_recipe_name
                        meal['Ingredients'] = selected_recipe['Ingredients']
                        meal['Recipe Link'] = selected_recipe['Recipe Link']
                        meal['Notes'] = selected_recipe['Notes']
                        break

                # Save the updated weekly menu to the Excel file
                weekly_menu_df = pd.DataFrame(st.session_state.all_meals_for_week)
                save_data(weekly_menu_df, EXCEL_FILE_PATH, sheet_name='Weekly Menu')
                st.session_state.all_meals_for_week = load_data(EXCEL_FILE_PATH, sheet_name='Weekly Menu').to_dict('records')
                st.success(f"{meal_type_to_edit} updated successfully for {day_to_edit}!")
    
    elif sidebar_option == "Recipes":
        st.subheader("All Recipes")
        # Sort the DataFrame alphabetically by "Recipe Name"
        df_sorted = st.session_state.data.sort_values(by="Recipe Name")
        
        # Mask links with "View Recipe"
        df_sorted['Recipe Link'] = df_sorted['Recipe Link'].apply(lambda x: f'<a href="{x}" target="_blank">View Recipe</a>' if pd.notna(x) else "N/A")
        
        # Display the DataFrame without an index
        st.write(df_sorted.to_html(escape=False, index=False), unsafe_allow_html=True)
        
        # Add a Recipe Button
        with st.expander("Add a New Recipe"):
            # Input fields for adding a new recipe
            recipe_name = st.text_input("Recipe Name", key="add_recipe_name")
            # Change meal_type to a multiselect with predefined options
            meal_types = st.multiselect("Meal Type", ["Breakfast", "Lunch", "Dinner"], key="add_meal_type")
            recipe_link = st.text_input("Recipe Link", key="add_recipe_link")
            ingredients = st.text_area("Ingredients", key="add_ingredients")
            notes = st.text_area("Notes", key="add_notes")
            
            # Submit button
            if st.button("Add Recipe", key="add_recipe_button"):
                if recipe_name in st.session_state.data['Recipe Name'].values:
                    st.error("Recipe with this name already exists!")
                else:
                    # Join the selected meal types into a single string
                    meal_type_str = ", ".join(meal_types)
                    new_recipe = {
                        "Recipe Name": recipe_name,
                        "Meal Type": meal_type_str,
                        "Recipe Link": recipe_link,
                        "Ingredients": ingredients,
                        "Notes": notes
                    }
                    new_recipe_df = pd.DataFrame([new_recipe])
                    st.session_state.data = pd.concat([st.session_state.data, new_recipe_df], ignore_index=True)
                    save_data(st.session_state.data, EXCEL_FILE_PATH)
                    st.success("Recipe added successfully!")
                    # Refresh data
                    st.session_state.data = load_data(EXCEL_FILE_PATH)

        # Edit a Recipe Button
        with st.expander("Edit a Recipe"):
            # Sort recipe names alphabetically for the dropdown
            sorted_recipe_names = sorted(st.session_state.data['Recipe Name'].unique())
            # Select a recipe to edit
            selected_recipe_name = st.selectbox("Select a Recipe to Edit", sorted_recipe_names)
            if selected_recipe_name:
                selected_recipe = st.session_state.data[st.session_state.data['Recipe Name'] == selected_recipe_name].iloc[0]
                # Editable fields
                edit_meal_type = st.text_input("Meal Type", selected_recipe['Meal Type'], key="edit_meal_type")
                edit_recipe_link = st.text_input("Recipe Link", selected_recipe['Recipe Link'], key="edit_recipe_link")
                edit_ingredients = st.text_area("Ingredients", selected_recipe['Ingredients'], key="edit_ingredients")
                edit_notes = st.text_area("Notes", selected_recipe['Notes'], key="edit_notes")
                
                # Save changes button
                if st.button("Save Changes", key="save_changes_button"):
                    st.session_state.data.loc[st.session_state.data['Recipe Name'] == selected_recipe_name, 'Meal Type'] = edit_meal_type
                    st.session_state.data.loc[st.session_state.data['Recipe Name'] == selected_recipe_name, 'Recipe Link'] = edit_recipe_link
                    st.session_state.data.loc[st.session_state.data['Recipe Name'] == selected_recipe_name, 'Ingredients'] = edit_ingredients
                    st.session_state.data.loc[st.session_state.data['Recipe Name'] == selected_recipe_name, 'Notes'] = edit_notes
                    save_data(st.session_state.data, EXCEL_FILE_PATH)
                    st.success("Recipe updated successfully!")
                    # Refresh data
                    st.session_state.data = load_data(EXCEL_FILE_PATH)

        # Delete a Recipe Button
        with st.expander("Delete a Recipe"):
            # Select a recipe to delete
            selected_recipe_name_to_delete = st.selectbox("Select a Recipe to Delete", sorted_recipe_names, key="delete_recipe_select")
            if st.button("Delete Recipe", key="delete_recipe_button"):
                st.session_state.data = st.session_state.data[st.session_state.data['Recipe Name'] != selected_recipe_name_to_delete]
                save_data(st.session_state.data, EXCEL_FILE_PATH)
                st.success("Recipe deleted successfully!")
                # Refresh data
                st.session_state.data = load_data(EXCEL_FILE_PATH)

if __name__ == "__main__":
    main()