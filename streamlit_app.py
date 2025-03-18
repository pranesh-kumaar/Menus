import streamlit as st
import pandas as pd
import random
from datetime import datetime
from streamlit_option_menu import option_menu

# Predefined Excel file path
EXCEL_FILE_PATH = r"Meals.xlsx"
st.set_page_config(page_title="Meal Planner", layout="wide")

# Function to load data from Excel
def load_data(file_path, sheet_name=0):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    return df

def save_data(data, file_path, sheet_name):
    # Try to load existing sheets first
    try:
        existing_sheets = pd.read_excel(file_path, sheet_name=None)  # Load all sheets
    except FileNotFoundError:
        existing_sheets = {}  # If the file doesn't exist, start fresh

    # Convert new data into a DataFrame
    df = pd.DataFrame(data)

    # Update the existing sheets with the new data
    existing_sheets[sheet_name] = df  # Replace or add the specific sheet

    # Save all sheets back to the Excel file
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        for sheet, df in existing_sheets.items():
            df.to_excel(writer, index=False, sheet_name=sheet)

# Convert weekly menu into a calendar-style DataFrame
def create_calendar_view(meal_data, available_recipes):
    # Define short day names
    short_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Create a dictionary to hold meal details for each day
    calendar_dict = {short_days[i]: {"Breakfast": "", "Lunch": "", "Dinner": ""} for i in range(7)}

    for meal in meal_data:
        day_short = short_days[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(meal["Day"])]
        calendar_dict[day_short][meal["Meal Type"]] = meal["Recipe Name"]

    # Convert to DataFrame
    calendar_df = pd.DataFrame.from_dict(calendar_dict, orient='index')

    # Convert meal columns to dropdowns with only available recipes (disable text input)
    column_config = {
        meal_type: st.column_config.SelectboxColumn(
            label=meal_type,
            options=available_recipes,  # Restrict selection to available recipes
            required=True  # Prevents blank values
        ) for meal_type in ["Breakfast", "Lunch", "Dinner"]
    }

    return calendar_df, column_config

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
    
    st.title("Meal Planner 🍽️")
    
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

    # Styled navigation bar
    nav_option = option_menu(
        menu_title="",  # Hide the default menu title
        options=["Generate Menu", "Menus", "Recipes", "Ingredients"],
        icons=["play-circle-fill", "map-fill", "table", "tablet-fill"],  # Empty icons for all options
        menu_icon="menu-button-wide",  # Icon for menu
        default_index=1,  # Default to "Menus"
        orientation="horizontal",
        styles={
            "nav-link": {"font-size": "16px", "text-align": "center", "margin": "5px"},
            "nav-link-selected": {"color": "white", "font-weight": "normal",},  # Highlight selected tab
        }
        
    )

    if nav_option == "Generate Menu":
        if st.button("Re-Generate Menu"):
            
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

                # Display the weekly menu
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        st.session_state.all_meals_for_week = load_data(EXCEL_FILE_PATH, sheet_name='Weekly Menu').to_dict('records')
        # for day in days_of_week:
        #     st.subheader(f"Recipes for {day}")
        #     day_meals = [meal for meal in st.session_state.all_meals_for_week if meal['Day'] == day]
        #     day_df = pd.DataFrame(day_meals).drop(columns=['Day'])
        #     day_df = day_df[['Meal Type', 'Recipe Name', 'Ingredients', 'Recipe Link', 'Notes']]
        #     day_df["Recipe Link"] = day_df["Recipe Link"].apply(
        #         lambda x: f"[View Recipe]({x})" if pd.notna(x) and x != "N/A" else "N/A"
        #     )
            #st.table(day_df[['Meal Type', 'Recipe Name', 'Recipe Link']].set_index("Meal Type"))

        # Load all available recipe names
        all_recipes_list = st.session_state.data["Recipe Name"].tolist()

        # Display the editable calendar view
        st.subheader("📅 Editable Weekly Meal Calendar")
        calendar_df, column_config = create_calendar_view(st.session_state.all_meals_for_week, all_recipes_list)

        # Enable in-line editing with restricted dropdowns
        edited_calendar_df = st.data_editor(
            calendar_df, 
            column_config=column_config, 
            num_rows="fixed",  # Ensures the number of rows doesn't change
            use_container_width=True
        )

        # Detect changes and update the session state
        if edited_calendar_df is not None and not edited_calendar_df.equals(calendar_df):
            # Update session state with new meal selections
            for day_short, meal_data in edited_calendar_df.iterrows():
                full_day = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].index(day_short)]
                
                for meal_type in ["Breakfast", "Lunch", "Dinner"]:
                    new_recipe_name = meal_data[meal_type]
                    
                    # Find the meal entry in session state and update it
                    for meal in st.session_state.all_meals_for_week:
                        if meal["Day"] == full_day and meal["Meal Type"] == meal_type:
                            meal["Recipe Name"] = new_recipe_name
                            # Update ingredients, link, and notes based on selected recipe
                            selected_recipe = st.session_state.data[st.session_state.data["Recipe Name"] == new_recipe_name].iloc[0]
                            meal["Ingredients"] = selected_recipe["Ingredients"]
                            meal["Recipe Link"] = selected_recipe["Recipe Link"] if pd.notna(selected_recipe["Recipe Link"]) else "N/A"
                            meal["Notes"] = selected_recipe["Notes"] if pd.notna(selected_recipe["Notes"]) else "N/A"

            # Save updated meals to Excel
            updated_menu_df = pd.DataFrame(st.session_state.all_meals_for_week)
            save_data(updated_menu_df, EXCEL_FILE_PATH, sheet_name="Weekly Menu")

            # Refresh session state
            st.session_state.all_meals_for_week = load_data(EXCEL_FILE_PATH, sheet_name="Weekly Menu").to_dict("records")
            st.rerun()
    
    elif nav_option == "Menus":
                
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
            today_df["Recipe Link"] = today_df["Recipe Link"].apply(
                    lambda x: f"[View Recipe]({x})" if pd.notna(x) and x != "N/A" else "N/A"
                )
            st.table(today_df[['Meal Type', 'Recipe Name', 'Recipe Link']].set_index("Meal Type"))
            with st.expander("Show All Details (Ingredients & Notes)"):
                for index, row in today_df.iterrows():
                    st.markdown(f"**{row['Meal Type']}**: {row['Recipe Name']}")
                    st.write(f"**Ingredients:** {row['Ingredients']}")
                    st.write(f"**Notes:** {row['Notes']}")
                    st.markdown("_")
        
        elif option == "View Tomorrow's Recipe":
            st.subheader(f"Recipes for {days_of_week[tomorrow_index]}")
            tomorrow_meals = [meal for meal in st.session_state.all_meals_for_week if meal['Day'] == days_of_week[tomorrow_index]]
            tomorrow_df = pd.DataFrame(tomorrow_meals).drop(columns=['Day'])
            tomorrow_df = tomorrow_df[['Meal Type', 'Recipe Name', 'Ingredients', 'Recipe Link', 'Notes']]
            tomorrow_df["Recipe Link"] = tomorrow_df["Recipe Link"].apply(
                    lambda x: f"[View Recipe]({x})" if pd.notna(x) and x != "N/A" else "N/A"
                )
            st.table(tomorrow_df[['Meal Type', 'Recipe Name', 'Recipe Link']].set_index("Meal Type"))
            with st.expander("Show All Details (Ingredients & Notes)"):
                for index, row in tomorrow_df.iterrows():
                    st.markdown(f"**{row['Meal Type']}**: {row['Recipe Name']}")
                    st.write(f"**Ingredients:** {row['Ingredients']}")
                    st.write(f"**Notes:** {row['Notes']}")
                    st.markdown("_")
        
        elif option == "View Week's Recipe":
            for day in days_of_week:
                st.subheader(f"Recipes for {day}")
                day_meals = [meal for meal in st.session_state.all_meals_for_week if meal['Day'] == day]
                day_df = pd.DataFrame(day_meals).drop(columns=['Day'])
                day_df = day_df[['Meal Type', 'Recipe Name', 'Ingredients', 'Recipe Link', 'Notes']]
                day_df["Recipe Link"] = day_df["Recipe Link"].apply(
                    lambda x: f"[View Recipe]({x})" if pd.notna(x) and x != "N/A" else "N/A"
                )
                st.table(day_df[['Meal Type', 'Recipe Name', 'Recipe Link']].set_index("Meal Type"))
                with st.expander("Show All Details (Ingredients & Notes)"):
                    for index, row in day_df.iterrows():
                        st.markdown(f"**{row['Meal Type']}**: {row['Recipe Name']}")
                        st.write(f"**Ingredients:** {row['Ingredients']}")
                        st.write(f"**Notes:** {row['Notes']}")
                        st.markdown("_")

    
    elif nav_option == "Recipes":
        st.subheader("All Recipes")
        # Reset index to bring "Recipe Name" back as a column
        st.session_state.data = load_data(EXCEL_FILE_PATH, sheet_name='Recipes')

        # Load and sort the recipes
        df_sorted = st.session_state.data.sort_values(by="Recipe Name")

        # Apply masked text for recipe link
        df_sorted["Recipe Link"] = df_sorted["Recipe Link"].apply(
                    lambda x: f"[View Recipe]({x})" if pd.notna(x) and x != "N/A" else "N/A"
                )

        # Display DataFrame with the masked link column
        st.table(df_sorted.set_index("Recipe Name"))

        
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
                    save_data(st.session_state.data, EXCEL_FILE_PATH, sheet_name='Recipes')
                    # Refresh data
                    st.session_state.data = load_data(EXCEL_FILE_PATH, sheet_name='Recipes')
                    st.rerun()

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
                    save_data(st.session_state.data, EXCEL_FILE_PATH, sheet_name='Recipes')
                    # Refresh data
                    st.session_state.data = load_data(EXCEL_FILE_PATH, sheet_name='Recipes')
                    st.rerun()

        # Delete a Recipe Button
        with st.expander("Delete a Recipe"):
            # Select a recipe to delete
            selected_recipe_name_to_delete = st.selectbox("Select a Recipe to Delete", sorted_recipe_names, key="delete_recipe_select")
            if st.button("Delete Recipe", key="delete_recipe_button"):
                st.session_state.data = st.session_state.data[st.session_state.data['Recipe Name'] != selected_recipe_name_to_delete]
                save_data(st.session_state.data, EXCEL_FILE_PATH, sheet_name='Recipes')
                # Refresh data
                st.session_state.data = load_data(EXCEL_FILE_PATH, sheet_name='Recipes')
                st.rerun()

if __name__ == "__main__":
    main()