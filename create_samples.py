"""
create_samples.py — Generate sample property brochure PDFs for testing.
Creates two brochures:
  1. Skyline Heights (all fields present)
  2. Greenview Residences (some fields missing)
"""

import os
import json
from fpdf import FPDF


class BrochurePDF(FPDF):
    """Custom PDF class for property brochures."""

    def header(self):
        self.set_fill_color(15, 12, 41)
        self.rect(0, 0, 210, 45, 'F')
        self.set_fill_color(48, 43, 99)
        self.rect(0, 45, 210, 5, 'F')

    def footer(self):
        self.set_y(-20)
        self.set_fill_color(15, 12, 41)
        self.rect(0, self.get_y(), 210, 25, 'F')
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(180, 180, 200)
        self.cell(0, 10, "This is a sample brochure for demonstration purposes only.", align="C")

    def add_title(self, title):
        self.set_y(12)
        self.set_font("Helvetica", "B", 26)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, title, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 11)
        self.set_text_color(180, 180, 220)
        self.cell(0, 8, "Premium Living Redefined", align="C", new_x="LMARGIN", new_y="NEXT")

    def add_section(self, title, content):
        self.ln(6)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(48, 43, 99)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

        self.set_draw_color(48, 43, 99)
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), self.get_x() + 40, self.get_y())
        self.ln(4)

        self.set_font("Helvetica", "", 11)
        self.set_text_color(50, 50, 60)
        self.multi_cell(0, 6, content)

    def add_highlights_box(self, items):
        self.ln(5)
        y_start = self.get_y()
        self.set_fill_color(240, 240, 250)
        self.rect(15, y_start, 180, len(items) * 9 + 14, 'F')
        self.set_draw_color(48, 43, 99)
        self.rect(15, y_start, 180, len(items) * 9 + 14, 'D')

        self.set_xy(20, y_start + 5)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(48, 43, 99)
        self.cell(0, 7, "Key Highlights", new_x="LMARGIN", new_y="NEXT")
        self.set_x(25)

        self.set_font("Helvetica", "", 10)
        self.set_text_color(60, 60, 70)
        for item in items:
            self.set_x(25)
            self.cell(5, 7, "-", new_x="END")
            self.cell(0, 7, f"  {item}", new_x="LMARGIN", new_y="NEXT")

        self.set_y(y_start + len(items) * 9 + 16)


def create_brochure_skyline():
    """Create Brochure 1: Skyline Heights — all fields present."""
    pdf = BrochurePDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    pdf.add_title("SKYLINE HEIGHTS")

    pdf.set_y(55)
    pdf.add_section(
        "Project Overview",
        "Skyline Heights is a premium residential development located in the heart of "
        "Sector 150, Noida, Uttar Pradesh. Designed by award-winning architects, this project "
        "offers a blend of luxury and comfort with world-class amenities and stunning views "
        "of the city skyline."
    )

    pdf.add_section(
        "Location",
        "Sector 150, Noida Expressway, Noida, Uttar Pradesh - 201310\n"
        "Near Botanical Garden Metro Station | 10 mins from FNG Expressway\n"
        "15 mins from DND Flyway | Close to top schools and hospitals"
    )

    pdf.add_section(
        "Unit Types & Pricing",
        "2 BHK Apartments: 1,050 sq.ft. - Starting at Rs. 85 Lakhs\n"
        "3 BHK Apartments: 1,450 sq.ft. - Starting at Rs. 1.05 Crore\n"
        "4 BHK Penthouse: 2,100 sq.ft. - Starting at Rs. 1.85 Crore\n\n"
        "Price Range: Rs. 85 Lakhs to Rs. 1.85 Crore (exclusive of taxes and registration)"
    )

    pdf.add_section(
        "Amenities",
        "Swimming Pool | Fully Equipped Gymnasium | Clubhouse with Banquet Hall\n"
        "Children's Play Area | Jogging Track | 24x7 Security with CCTV\n"
        "Landscaped Gardens | Indoor Badminton Court | Meditation Zone\n"
        "EV Charging Stations | Smart Home Features | Covered Parking"
    )

    pdf.add_section(
        "Possession Details",
        "Expected Possession: December 2027\n"
        "RERA Registration No: UPRERAPRJ12345\n"
        "Total Units: 450 | Total Towers: 4 | Floors: G+25"
    )

    pdf.add_highlights_box([
        "Vastu Compliant Design",
        "Earthquake Resistant Structure (Zone IV)",
        "Rainwater Harvesting System",
        "100% Power Backup for Common Areas",
        "2 Dedicated Car Parking Per Unit",
    ])

    os.makedirs("sample_inputs", exist_ok=True)
    pdf.output("sample_inputs/brochure_skyline.pdf")
    print("Created: sample_inputs/brochure_skyline.pdf")


def create_brochure_greenview():
    """Create Brochure 2: Greenview Residences — missing price & possession date."""
    pdf = BrochurePDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    pdf.add_title("GREENVIEW RESIDENCES")

    pdf.set_y(55)
    pdf.add_section(
        "About the Project",
        "Greenview Residences is an upcoming residential development situated along the "
        "Dwarka Expressway in Gurgaon, Haryana. Surrounded by lush greenery and "
        "open spaces, this project is designed for families who value nature and "
        "modern living."
    )

    pdf.add_section(
        "Location",
        "Sector 103, Dwarka Expressway, Gurgaon, Haryana - 122006\n"
        "Adjacent to proposed Metro corridor | Near Diplomatic Enclave\n"
        "20 mins from IGI Airport | Well connected to NH-8"
    )

    pdf.add_section(
        "Available Configurations",
        "2 BHK Apartments: 950 sq.ft. carpet area\n"
        "3 BHK Apartments: 1,400 sq.ft. carpet area\n\n"
        "All apartments feature large balconies, modular kitchen provisions, "
        "and cross-ventilation design for natural airflow."
    )

    pdf.add_section(
        "Amenities & Facilities",
        "Landscaped Central Garden with Walking Paths\n"
        "Covered Car Parking Facility\n"
        "Children's Playground with Safety Flooring\n"
        "Multipurpose Community Hall\n"
        "24/7 Water Supply and Power Backup\n"
        "Gated Community with Security Personnel"
    )

    pdf.add_section(
        "Developer Information",
        "Developed by GreenBuild Infratech Pvt. Ltd.\n"
        "Over 15 years of experience in residential construction.\n"
        "Contact: info@greenbuildinfra.example.com | +91-98765-43210"
    )

    pdf.add_highlights_box([
        "Green Building Certified (IGBC Pre-certified)",
        "70% Open Area with Dense Plantation",
        "Dedicated Senior Citizen Zone",
        "Proximity to Upcoming Metro Station",
        "Pet-Friendly Community Spaces",
    ])

    os.makedirs("sample_inputs", exist_ok=True)
    pdf.output("sample_inputs/brochure_greenview.pdf")
    print("Created: sample_inputs/brochure_greenview.pdf")


def create_sample_outputs():
    """Create expected JSON outputs for each sample brochure."""
    skyline_output = {
        "project_name": {"value": "Skyline Heights", "confidence": "high"},
        "location_address": {"value": "Sector 150, Noida Expressway, Noida, Uttar Pradesh - 201310", "confidence": "high"},
        "price_range": {"value": "Rs. 85 Lakhs to Rs. 1.85 Crore", "confidence": "high"},
        "unit_types": {"value": "2 BHK, 3 BHK, 4 BHK Penthouse", "confidence": "high"},
        "area": {"value": "1,050 sq.ft. to 2,100 sq.ft.", "confidence": "high"},
        "amenities": {"value": "Swimming Pool, Gymnasium, Clubhouse, Children's Play Area, Jogging Track, 24x7 Security, Landscaped Gardens, Badminton Court, Meditation Zone, EV Charging, Smart Home, Covered Parking", "confidence": "high"},
        "possession_date": {"value": "December 2027", "confidence": "high"}
    }

    greenview_output = {
        "project_name": {"value": "Greenview Residences", "confidence": "high"},
        "location_address": {"value": "Sector 103, Dwarka Expressway, Gurgaon, Haryana - 122006", "confidence": "high"},
        "price_range": {"value": "Not found", "confidence": "not_found"},
        "unit_types": {"value": "2 BHK, 3 BHK", "confidence": "high"},
        "area": {"value": "950 sq.ft. to 1,400 sq.ft.", "confidence": "high"},
        "amenities": {"value": "Landscaped Garden, Car Parking, Children's Playground, Community Hall, 24/7 Water Supply, Power Backup, Gated Security", "confidence": "high"},
        "possession_date": {"value": "Not found", "confidence": "not_found"}
    }

    os.makedirs("sample_outputs", exist_ok=True)
    
    with open("sample_outputs/skyline_output.json", "w", encoding="utf-8") as f:
        json.dump(skyline_output, f, indent=2, ensure_ascii=False)
    print("Created: sample_outputs/skyline_output.json")

    with open("sample_outputs/greenview_output.json", "w", encoding="utf-8") as f:
        json.dump(greenview_output, f, indent=2, ensure_ascii=False)
    print("Created: sample_outputs/greenview_output.json")


if __name__ == "__main__":
    create_brochure_skyline()
    create_brochure_greenview()
    create_sample_outputs()
    print("\nAll sample files created successfully!")
