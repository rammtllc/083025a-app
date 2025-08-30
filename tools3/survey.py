from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this in production

# MySQL connection config
db_config = {
    "host": "localhost",
    "user": "root",      # your DB user
    "password": "",      # your DB password
    "database": "stixtricks"
}

# Get all unique chapter base names (ignore (Short) and (Long))
def get_unique_chapters():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT chapter_name FROM youtube_scripts ORDER BY id")
    all_chapters = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    unique_base_chapters = []
    seen = set()
    for chapter in all_chapters:
        base = chapter.replace("(Short)", "").replace("(Long)", "").strip()
        if base not in seen:
            seen.add(base)
            unique_base_chapters.append(base)
    return unique_base_chapters

# Get all rows for a given base chapter name
def get_rows_for_chapter(base_chapter_name):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, chapter_name FROM youtube_scripts")
    rows = []
    for row in cursor.fetchall():
        row_id, content, chapter_name = row
        base = chapter_name.replace("(Short)", "").replace("(Long)", "").strip()
        if base == base_chapter_name:
            rows.append((row_id, content))
    cursor.close()
    conn.close()
    return rows

@app.route("/", methods=["GET"])
def index():
    session.clear()
    return redirect(url_for("survey_page", page=0))

@app.route("/survey/<int:page>", methods=["GET", "POST"])
def survey_page(page):
    unique_chapters = get_unique_chapters()
    if page >= len(unique_chapters):
        return redirect(url_for("survey_results"))

    base_chapter = unique_chapters[page]

    # Fetch all rows for this base chapter
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, content, chapter_name FROM youtube_scripts WHERE chapter_name LIKE %s ORDER BY id",
        (f"%{base_chapter}%",)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    options = [(row[0], f"{row[2]}: {row[1][:100]}{'...' if len(row[1]) > 100 else ''}") for row in rows]

    if request.method == "POST":
        selected_ids = request.form.getlist("answer[]")
        selected_ids = [int(i) for i in selected_ids if i and i.isdigit()]

        if "answers" not in session:
            session["answers"] = []

        # Remove previous selections for this page
        session["answers"] = [a for a in session["answers"] if a["chapter"] != base_chapter]

        # Append current selections
        for ans_id in selected_ids:
            session["answers"].append({"id": ans_id, "chapter": base_chapter})

        next_page = page + 1
        if next_page >= len(unique_chapters):
            return redirect(url_for("survey_results"))
        return redirect(url_for("survey_page", page=next_page))

    selected_ids = [str(a["id"]) for a in session.get("answers", []) if a["chapter"] == base_chapter]

    return render_template(
        "survey_page.html",
        page=page,
        total_pages=len(unique_chapters),
        chapter=base_chapter,
        options=options,
        selected_ids=selected_ids
    )


@app.route("/results")
def survey_results():
    answers = session.get("answers", [])
    results_data = []

    if not answers:
        return render_template("results.html", results=[])

    # Connect once and fetch all contents in order of answers
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    for ans in answers:
        cursor.execute("SELECT content FROM youtube_scripts WHERE id = %s", (ans["id"],))
        row = cursor.fetchone()
        if row:
            results_data.append((ans["chapter"], row[0]))

    cursor.close()
    conn.close()

    return render_template("results.html", results=results_data)

from openai import OpenAI

client = OpenAI()

@app.route("/generate")
def generate_results():
    answers = session.get("answers", [])
    if not answers:
        return render_template("results.html", results=[])

    # Collect all selected text
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    collected_texts = []
    for ans in answers:
        cursor.execute("SELECT content FROM youtube_scripts WHERE id = %s", (ans["id"],))
        row = cursor.fetchone()
        if row:
            collected_texts.append(row[0])
    cursor.close()
    conn.close()

    # Combine into a single raw input text
    raw_text = "\n\n".join(collected_texts)

    # Define your transformation prompts
    prompts = [
        "Rewrite this content in a clear, organized format suitable for a YouTube guide. Break it into Introduction, Chapters, and Conclusion. Keep the tone conversational and instructional.",
        "Convert this into a YouTube script with a natural flow, including hooks, transitions, and chapter headings. Make it sound like I’m speaking to the camera.",
        "Enhance the script by adding suggested B-roll clips, stock footage ideas, and visual overlays for each scene so an editor can follow along.",
        "Include text animations, on-screen graphics, and editing cues per scene to make this a full production-ready YouTube script.",
        "Add timestamps to each section or chapter so it’s easier to edit and structure the video.",
        """Take this raw YouTube guide text and turn it into a full production-ready script:

        Organize into Introduction, Chapters, and Conclusion
        Add hooks and transitions
        Suggest B-roll, stock footage, and overlays for each scene
        Include text animations and on-screen graphics
        Add timestamps for each section
        Keep a conversational, instructional tone suitable for small creators in 2025"""
    ]

    # Run the chain of prompts
    previous_output = raw_text
    #for prompt in prompts:
    #    response = client.chat.completions.create(
    #        model="gpt-4.1-mini",
    #        messages=[
    #            {"role": "system", "content": "You are a helpful assistant for YouTube content strategy and scriptwriting."},
    #            {"role": "user", "content": f"{prompt}\n\nHere is the text to work with:\n{previous_output}"}
    #        ]
    #    )
    #    previous_output = response.choices[0].message["content"]

    for prompt in prompts:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",  # or gpt-4.1
             messages=[
                {"role": "system", "content": "You are a helpful assistant for YouTube content strategy and scriptwriting."},
                {"role": "user", "content": f"{prompt}\n\nHere is the text to work with:\n{previous_output}"}
            ]
        )

    # Correct way to extract the content
        previous_output = response.choices[0].message.content

    # Send the final output to a new template
    return render_template("generate_results.html", output=previous_output)


if __name__ == "__main__":
    app.run(debug=True)
