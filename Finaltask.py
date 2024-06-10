import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import pyodbc

def connect_to_db():
    username = username_entry.get()
    password = password_entry.get()
    
    try:
        connection = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER=localhost;'
            f'DATABASE=farmersmarkets;'
            f'UID={username};'
            f'PWD={password}'
        )
        messagebox.showinfo("Connection Status", "Connected to the database successfully")
        list_tables(connection)
    except Exception as e:
        messagebox.showerror("Connection Status", f"Failed to connect to the database. Error: {str(e)}")

def list_tables(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    
    tables = cursor.fetchall()
    for table in tables:
        tables_listbox.insert(tk.END, table.TABLE_NAME)
    
    connection.close()

def view_table(search_criteria=None, min_criteria=None, max_criteria=None):
    global tree
    
    try:
        selected_table = tables_listbox.get(tables_listbox.curselection())
        username = username_entry.get()
        password = password_entry.get()
        
        connection = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER=localhost;'
            f'DATABASE=farmersmarkets;'
            f'UID={username};'
            f'PWD={password}'
        )
        
        cursor = connection.cursor()
        query = f"SELECT * FROM {selected_table}"
        
        conditions = []
        values = []
        
        if search_criteria:
            for col, val in search_criteria.items():
                conditions.append(f"{col} LIKE ?")
                values.append(f"%{val}%")
        
        if min_criteria:
            for col, val in min_criteria.items():
                conditions.append(f"{col} >= ?")
                values.append(val)
        
        if max_criteria:
            for col, val in max_criteria.items():
                conditions.append(f"{col} <= ?")
                values.append(val)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        cursor.execute(query, values)
        
        rows = cursor.fetchall()
        
        columns = [column[0] for column in cursor.description]
        tree["columns"] = columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.delete(*tree.get_children())  # Clear previous data
        
        for row in rows:
            tree.insert("", "end", values=[str(value) for value in row])
        
        global current_table
        current_table = selected_table
        connection.close()
    except Exception as e:
        messagebox.showerror("Table View Error", f"Failed to retrieve table contents. Error: {str(e)}")

def search_data():
    selected_table = tables_listbox.get(tables_listbox.curselection())
    
    def submit():
        search_criteria = {col: entry.get() for col, entry in zip(column_names, entries) if entry.get()}
        min_criteria = {col: entry.get() for col, entry in zip(column_names, min_entries) if entry.get()}
        max_criteria = {col: entry.get() for col, entry in zip(column_names, max_entries) if entry.get()}
        search_window.destroy()
        view_table(search_criteria, min_criteria, max_criteria)
    
    search_window = tk.Toplevel(app)
    search_window.title(f"Search in {selected_table}")
    search_window.transient(app)  # Set the main app window as the parent
    search_window.grab_set()  # Make the search window modal
    
    connection = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER=localhost;'
        f'DATABASE=farmersmarkets;'
        f'UID={username_entry.get()};'
        f'PWD={password_entry.get()}'
    )
    cursor = connection.cursor()
    cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{selected_table}'")
    columns = cursor.fetchall()
    column_names = [col.COLUMN_NAME for col in columns]
    
    entries = []
    min_entries = []
    max_entries = []
    
    for idx, column in enumerate(column_names):
        label = tk.Label(search_window, text=column)
        label.grid(row=idx, column=0)
        entry = tk.Entry(search_window)
        entry.grid(row=idx, column=1)
        entries.append(entry)
        
        min_label = tk.Label(search_window, text=f"Min {column}")
        min_label.grid(row=idx, column=2)
        min_entry = tk.Entry(search_window)
        min_entry.grid(row=idx, column=3)
        min_entries.append(min_entry)
        
        max_label = tk.Label(search_window, text=f"Max {column}")
        max_label.grid(row=idx, column=4)
        max_entry = tk.Entry(search_window)
        max_entry.grid(row=idx, column=5)
        max_entries.append(max_entry)
    
    submit_button = tk.Button(search_window, text="Submit", command=submit)
    submit_button.grid(row=len(column_names), column=0, columnspan=6)


def add_data():
    selected_table = current_table
    column_names = [tree.heading(col)["text"] for col in tree["columns"]]
    
    def submit():
        username = username_entry.get()
        password = password_entry.get()
        values = [entry.get() for entry in entries]
        
        try:
            connection = pyodbc.connect(
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER=localhost;'
                f'DATABASE=farmersmarkets;'
                f'UID={username};'
                f'PWD={password}'
            )
            cursor = connection.cursor()
            placeholders = ', '.join(['?' for _ in values])
            query = f"INSERT INTO {selected_table} ({', '.join(column_names)}) VALUES ({placeholders})"
            cursor.execute(query, values)
            connection.commit()
            connection.close()
            add_window.destroy()
            view_table()
        except Exception as e:
            messagebox.showerror("Add Data Error", f"Failed to add data. Error: {str(e)}")
    
    add_window = tk.Toplevel(app)
    add_window.title(f"Add Data to {selected_table}")
    
    entries = []
    for idx, column in enumerate(column_names):
        label = tk.Label(add_window, text=column)
        label.grid(row=idx, column=0)
        entry = tk.Entry(add_window)
        entry.grid(row=idx, column=1)
        entries.append(entry)
    
    submit_button = tk.Button(add_window, text="Submit", command=submit)
    submit_button.grid(row=len(column_names), column=0, columnspan=2)

def update_data():
    selected_table = current_table
    column_names = [tree.heading(col)["text"] for col in tree["columns"]]
    selected_item = tree.selection()[0]
    old_values = tree.item(selected_item, "values")
    
    def submit():
        username = username_entry.get()
        password = password_entry.get()
        new_values = [entry.get() for entry in entries]
        
        try:
            connection = pyodbc.connect(
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER=localhost;'
                f'DATABASE=farmersmarkets;'
                f'UID={username};'
                f'PWD={password}'
            )
            cursor = connection.cursor()
            set_clause = ', '.join([f"{col} = ?" for col in column_names])
            query = f"UPDATE {selected_table} SET {set_clause} WHERE {column_names[0]} = ?"
            cursor.execute(query, new_values + [old_values[0]])
            connection.commit()
            connection.close()
            update_window.destroy()
            view_table()
        except Exception as e:
            messagebox.showerror("Update Data Error", f"Failed to update data. Error: {str(e)}")
    
    update_window = tk.Toplevel(app)
    update_window.title(f"Update Data in {selected_table}")
    
    entries = []
    for idx, (column, old_value) in enumerate(zip(column_names, old_values)):
        label = tk.Label(update_window, text=column)
        label.grid(row=idx, column=0)
        entry = tk.Entry(update_window)
        entry.insert(0, old_value)
        entry.grid(row=idx, column=1)
        entries.append(entry)
    
    submit_button = tk.Button(update_window, text="Submit", command=submit)
    submit_button.grid(row=len(column_names), column=0, columnspan=2)

def delete_data():
    selected_table = current_table
    column_names = [tree.heading(col)["text"] for col in tree["columns"]]
    selected_item = tree.selection()[0]
    values = tree.item(selected_item, "values")
    
    username = username_entry.get()
    password = password_entry.get()
    
    try:
        connection = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER=localhost;'
            f'DATABASE=farmersmarkets;'
            f'UID={username};'
            f'PWD={password}'
        )
        cursor = connection.cursor()
        query = f"DELETE FROM {selected_table} WHERE {column_names[0]} = ?"
        cursor.execute(query, values[0])
        connection.commit()
        connection.close()
        view_table()
    except Exception as e:
        messagebox.showerror("Delete Data Error", f"Failed to delete data. Error: {str(e)}")


# Set up the main application window
app = tk.Tk()
app.title("SQL Server Database Browser")

# Set the geometry of the window to open as a rectangle
app.geometry("800x600")

# Username label and entry
username_label = tk.Label(app, text="Username:")
username_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
username_entry = tk.Entry(app)
username_entry.grid(row=0, column=1, padx=10, pady=10)

# Password label and entry
password_label = tk.Label(app, text="Password:")
password_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
password_entry = tk.Entry(app, show="*")
password_entry.grid(row=1, column=1, padx=10, pady=10)

# Connect button
connect_button = tk.Button(app, text="Connect", command=connect_to_db)
connect_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

# Tables list label
tables_label = tk.Label(app, text="Tables:")
tables_label.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)

# Tables listbox
tables_listbox = tk.Listbox(app, exportselection=False)
tables_listbox.grid(row=3, column=1, padx=10, pady=10)

# View button
view_button = tk.Button(app, text="View Table", command=view_table)
view_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

# Add data button
add_button = tk.Button(app, text="Add Data", command=add_data)
add_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

# Update data button
update_button = tk.Button(app, text="Update Data", command=update_data)
update_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

# Delete data button
delete_button = tk.Button(app, text="Delete Data", command=delete_data)
delete_button.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

# Search data button
search_button = tk.Button(app, text="Search Data", command=search_data)
search_button.grid(row=8, column=0, columnspan=2, padx=10, pady=10)

# Treeview for displaying table data
tree = ttk.Treeview(app)
tree.grid(row=0, column=2, rowspan=10, padx=10, pady=10, sticky=tk.NSEW)

# Configure grid weights to make the treeview expand properly
app.grid_columnconfigure(2, weight=1)
app.grid_rowconfigure(9, weight=1)

# Start the main loop
app.mainloop()

