from flask import Flask, request, render_template
import pandas as pd

app = Flask(__name__)

# Load data
iit_df = pd.read_csv("data/iit.csv")
nit_df = pd.read_csv("data/nit.csv")
iiit_df = pd.read_csv("data/iiit.csv")
gfti_df = pd.read_csv("data/gfti.csv")

# Standardize columns and convert ranks to numeric (this thing can be treated as a pre-processing step)
for df in [iit_df, nit_df, iiit_df, gfti_df]:
    df.columns = df.columns.str.strip().str.lower()
    df["opening rank"] = pd.to_numeric(df["opening rank"], errors="coerce")
    df["closing rank"] = pd.to_numeric(df["closing rank"], errors="coerce")
    df.dropna(subset=["closing rank"], inplace=True)  # keep those with closing rank

# College-state mapping
# Enhanced and more comprehensive mapping
college_state_mapping = {
    # NITs
    "tiruchirappalli": "tamil nadu",
    "trichy": "tamil nadu",
    "surathkal": "karnataka",
    "warangal": "telangana",
    "calicut": "kerala",
    "rourkela": "odisha",
    "durgapur": "west bengal",
    "hamirpur": "himachal pradesh",
    "jaipur": "rajasthan",
    "jalandhar": "punjab",
    "jamshedpur": "jharkhand",
    "nagpur": "maharashtra",
    "silchar": "assam",
    "agartala": "tripura",
    "patna": "bihar",
    "raipur": "chhattisgarh",
    "bhopal": "madhya pradesh",
    "kurukshetra": "haryana",
    "srinagar": "jammu and kashmir",
    "goa": "goa",
    "mizoram": "mizoram",
    "arunachal": "arunachal pradesh",
    "uttarakhand": "uttarakhand",
    "manipur": "manipur",
    "meghalaya": "meghalaya",
    "nagaland": "nagaland",
    "puducherry": "puducherry",
    
    # IITs
    "bombay": "maharashtra",
    "delhi": "delhi",
    "madras": "tamil nadu",
    "kanpur": "uttar pradesh",
    "kharagpur": "west bengal",
    "roorkee": "uttarakhand",
    "guwahati": "assam",
    "bhilai": "chhattisgarh",
    "goa": "goa",
    "dhanbad": "jharkhand",
    "mandi": "himachal pradesh",
    "jodhpur": "rajasthan",
    "palakkad": "kerala",
    "tirupati": "andhra pradesh",
    "indore": "madhya pradesh",
    "patna": "bihar",
    "ism": "jharkhand",

    # IIITs (some examples)
    "iiit hyderabad": "telangana",
    "iiit delhi": "delhi",
    "iiit bangalore": "karnataka",
    "iiit allahabad": "uttar pradesh",
    "iiitdm kancheepuram": "tamil nadu",
    "iiitdm jabalpur": "madhya pradesh",
    "iiit kottayam": "kerala",
    "iiit sricity": "andhra pradesh",

    # GFTIs
    "bit mesra": "jharkhand",
    "assam university": "assam",
    "gurukula kangri": "uttarakhand",
    "pec chandigarh": "chandigarh",
    "ism dhanbad": "jharkhand",
    "lnmiit": "rajasthan",
}

priority_order = {
    "computer science and engineering": 1,
    "electronics and communication engineering": 2,
    "electrical engineering": 3,
    "mechanical engineering": 4,
    "chemical engineering": 5,
    "civil engineering": 6
}

##pre-process the csvs to convert the iit names into redable ones (later)
iit_priority_order = {
    "indian institute of technology madras": 1,
    "indian institute of technology delhi": 2,
    "indian institute of technology bombay": 3,
    "indian institute of technology kanpur": 4,
    "indian institute of technology kharagpur": 5,
    "indian institute of technology roorkee": 6,
    "indian institute of technology guwahati": 7,
    "indian institute of technology hyderabad": 8,
    "indian institute of technology (bhu) varanasi": 9,
    "indian institute of technology (ism) dhanbad": 10,
    "indian institute of technology indore": 11,
    "indian institute of technology ropar": 12,
    "indian institute of technology mandi": 13,
    "indian institute of technology gandhinagar": 14,
    "indian institute of technology jodhpur": 15,
    "indian institute of technology patna": 16,
    "indian institute of technology bhubaneshwar": 17,
    "indian institute of technology tirupati": 18,
    "indian institute of technology palakkad": 19,
    "indian institute of technology jammu": 20,
    "indian institute of technology dharwad": 21,
    "indian institute of technology bhilai": 22
}

gender_mapping = {
    'male': 'gender-neutral',
    'female': 'female-only (including supernumerary)',
    'donot-specify': 'gender-neutral'
}

def get_college_state(college_name):
    college_name_lower = college_name.lower()
    return college_state_mapping.get(college_name_lower)

def get_branch_priority(branch):
    branch_lower = branch.lower()
    search_result = priority_order.get(branch_lower)
    if search_result is None:
        return 999
    return search_result
    
def get_iit_priority(institute_name):
    institute_name_lower = institute_name.lower()
    search_result = iit_priority_order.get(institute_name_lower)
    if search_result is None:
        return 999
    return search_result

def get_gender(gender):
    gender_lower = gender.lower()
    return gender_mapping.get(gender_lower).lower()

@app.route("/", methods=["GET", "POST"])
def home():
    results_html = None
    if request.method == "POST":
        rank = int(request.form["rank"])
        category = request.form["category"].strip().upper()
        gender = request.form["gender"].strip().lower()
        exam_type = request.form["exam"].strip().lower()
        user_state = request.form["state"].strip().lower()

        if exam_type == "advanced":
            df = iit_df
            filtered = df[
                (df["seat type"].str.upper() == category) &
                (df["closing rank"] > rank) &
                (df["gender"].str.lower() == get_gender(gender))
            ].copy()


            # Sort by IIT priority
            filtered["iit_priority"] = filtered["institute"].map(lambda x: get_iit_priority(str(x)))
            filtered = filtered.sort_values(by="iit_priority", ascending=True)


        else:
            df_all = pd.concat([nit_df, iiit_df, gfti_df])
            df_all["user_quota"] = df_all["institute"].apply(
                lambda x: "HS" if get_college_state(x) == user_state.lower() else "OS"
            )


            filtered = df_all[
                (df_all["seat type"].str.upper() == category) &
                (df_all["closing rank"] >= rank) &
                (df["gender"].str.lower() == get_gender(gender))
            ].copy()

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
