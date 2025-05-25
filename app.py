from flask import Flask, request, render_template
import pandas as pd

app = Flask(__name__)

# Load data
iit_df = pd.read_excel("data/iit.xlsx")
nit_df = pd.read_excel("data/nit.xlsx")
iiit_df = pd.read_excel("data/iiit.xlsx")
gfti_df = pd.read_excel("data/gfti.xlsx")

# Standardize columns and convert ranks to numeric
for df in [iit_df, nit_df, iiit_df, gfti_df]:
    df.columns = df.columns.str.strip().str.lower()
    df["opening rank"] = pd.to_numeric(df["opening rank"], errors="coerce")
    df["closing rank"] = pd.to_numeric(df["closing rank"], errors="coerce")
    df.dropna(subset=["closing rank"], inplace=True)  # keep those with closing rank

# College-state mapping
college_state_mapping = {
    "patna": "bihar", "bhopal": "madhya pradesh", "raipur": "chhattisgarh",
    "jamshedpur": "jharkhand", "durgapur": "west bengal", "jalandhar": "punjab",
    "delhi": "delhi", "calicut": "kerala", "surathkal": "karnataka",
    "tiruchirappalli": "tamil nadu", "warangal": "telangana", "rourkela": "odisha",
    "allahabad": "uttar pradesh", "silchar": "assam", "hamirpur": "himachal pradesh",
    "kurukshetra": "haryana", "jaipur": "rajasthan", "jodhpur": "rajasthan",
    "surat": "gujarat", "vadodara": "gujarat", "goa": "goa",
    "visvesvaraya": "maharashtra", "agartala": "tripura", "manipur": "manipur",
    "meghalaya": "meghalaya", "mizoram": "mizoram", "nagaland": "nagaland",
    "sikkim": "sikkim", "arunachal pradesh": "arunachal pradesh", "puducherry": "puducherry"
}

priority_order = {
    "Computer Science and Engineering": 1,
    "Electronics and Communication Engineering": 2,
    "Electrical Engineering": 3,
    "Mechanical Engineering": 4,
    "Chemical Engineering": 5,
    "Civil Engineering": 6
}
iit_priority_order = {
    "IIT Madras": 1,
    "IIT Delhi": 2,
    "IIT Bombay": 3,
    "IIT Kanpur": 4,
    "IIT Kharagpur": 5,
    "IIT Roorkee": 6,
    "IIT Guwahati": 7,
    "IIT Hyderabad": 8,
    "IIT BHU": 9,
    "IIT ISM Dhanbad": 10,
    "IIT Indore": 11,
    "IIT Ropar": 12,
    "IIT Mandi": 13,
    "IIT Gandhinagar": 14,
    "IIT Jodhpur": 15,
    "IIT Patna": 16,
    "IIT Bhubaneshwar": 17,
    "IIT Tirupati": 18,
    "IIT Palakkad": 19,
    "IIT Jammu": 20,
    "IIT Dharwad": 21,
    "IIT Bhilai": 22
}


def get_branch_priority(branch):
    return priority_order.get(branch.strip(), 999)
def get_iit_priority(institute_name):
    for name, priority in iit_priority_order.items():
        if name.lower() in institute_name.lower():
            return priority
    return 999  # default low priority for unknown colleges


def get_quota(institute, user_state):
    for keyword, state in college_state_mapping.items():
        if keyword.lower() in institute.lower():
            return "HS" if user_state == state else "OS"
    return "OS"

@app.route("/", methods=["GET", "POST"])
def home():
    results_html = None
    if request.method == "POST":
        rank = int(request.form["rank"])
        category = request.form["category"].strip().upper()
        exam_type = request.form["exam"].strip().lower()
        user_state = request.form["state"].strip().lower()

        if exam_type == "advanced":
            df = iit_df
            filtered = df[
            (df["seat type"].str.upper() == category) &
            (df["closing rank"] > rank)  # <-- note: changed to strict comparison
    ]

            # Sort by IIT priority
            filtered = filtered.sort_values(
                by="institute",
                key=lambda col: col.map(lambda x: get_iit_priority(str(x))),
                ascending=True
            )

        else:
            df_all = pd.concat([nit_df, iiit_df, gfti_df])
            df_all["user_quota"] = df_all["institute"].apply(lambda x: get_quota(str(x), user_state))

            filtered = df_all[
                (df_all["seat type"].str.upper() == category) &
                (df_all["closing rank"] >= rank)
            ]

            # Prefer HS quota if any match exists
            hs_filtered = filtered[filtered["user_quota"] == "HS"]
            if not hs_filtered.empty:
                filtered = hs_filtered
            else:
                filtered = filtered[filtered["user_quota"] == "OS"]

            filtered = filtered.sort_values(
                by="academic program name",
                key=lambda col: col.map(lambda x: get_branch_priority(str(x))),
                ascending=True
            )

        eligible = filtered

        if eligible.empty:
            results_html = '''
            <div class="card-container">
                <div class="college-box">No colleges available at this rank for your selection.</div>
            </div>
            '''
        else:
            results_html = '<div class="card-container">'
            for i in range(0, len(eligible), 3):
                results_html += '<div class="card-row">'
                for _, row in eligible.iloc[i:i+3].iterrows():
                    results_html += f'''
                    <div class="college-box">
                        <h3>{row.get('institute', 'N/A')}</h3>
                        <p><strong>Program:</strong> {row.get('academic program name', 'N/A')}</p>
                        <p><strong>Quota:</strong> {row.get('user_quota', '')}, <strong>Gender:</strong> {row.get('gender', 'Gender-Neutral')}</p>
                        <p><strong>Category:</strong> {row.get('seat type', 'N/A')}</p>
                        <p><strong>Opening Rank:</strong> {row.get('opening rank', 'N/A')}, <strong>Closing Rank:</strong> {row.get('closing rank', 'N/A')}</p>
                    </div>
                    '''
                results_html += '</div>'
            results_html += '</div>'

    return render_template("index.html", results=results_html)

if __name__ == "__main__":
    app.run(debug=True)
