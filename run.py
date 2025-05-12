from act4community import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) # Laissez debug=True pour le développement