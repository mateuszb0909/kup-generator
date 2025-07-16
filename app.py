import streamlit as st
import datetime
import json
import os
import re
import time
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Konfiguracja ---
PLIK_HISTORII = "historia_okresow.json"
FOLDER_PDF = "Ready PDFs"
URL_REGEX = re.compile(r'^(https?):\/\/[^\s/$.?#].[^\s]*$')
PLIK_PODPISU_ZAPISANEGO = "podpis_uzytkownika.png"

try:
    pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'DejaVuSans-Bold.ttf'))
    FONT_NAME = 'DejaVu'
    FONT_BOLD = 'DejaVu-Bold'
except IOError:
    FONT_NAME = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'
    
#======================================================================
#  SŁOWNIK TŁUMACZEŃ DLA UI
#======================================================================
translations = {
    'pl': {
        'page_title': "Generator Oświadczeń", 'app_title': "📄 Generator Oświadczeń Pracownika",
        'settings_header': "⚙️ Ustawienia", 'lang_select_label': "Język interfejsu",
        'signature_header': "✍️ Podpis", 'upload_label': "Wybierz plik PNG z podpisem",
        'upload_help': "Wgrany plik zostanie użyty w generowanym dokumencie.",
        'signature_success': "Podpis został wgrany i zapisany!",
        'current_signature': "Aktualnie używany podpis:", 'delete_signature_button': "🗑️ Usuń zapisany podpis",
        'signature_deleted': "Zapisany podpis został usunięty.", 'no_signature_to_delete': "Brak zapisanego podpisu do usunięcia.",
        'no_signature': "Brak wgranego lub zapisanego podpisu.", 'history_header': "🗓️ Historia okresów",
        'last_date_label': "Ostatnia zapisana data końcowa:", 'no_history': "Brak",
        'overwrite_date_label': "Nadpisz datę", 'save_history_button': "💾 Zapisz historię",
        'history_updated': "Historia zaktualizowana!", 'font_warning': "Brak czcionek DejaVu. Polskie znaki mogą nie działać poprawnie.",
        'add_works_header': "1. Dodaj wykonane utwory", 'project_name_label': "Nazwa projektu",
        'work_desc_label': "Opis wykonanej pracy", 'add_work_button': "➕ Dodaj utwór do listy",
        'works_list_header': "**Lista dodanych utworów:**", 'delete_entry_help': "Usuń ten wpis",
        'other_data_header': "2. Podaj pozostałe dane", 'link_label': "Wspólny link do ewidencji (np. https://...)",
        'period_select_header': "Wybór okresu rozliczeniowego", 'period_auto': "Automatycznie (zalecane)", 'period_manual': "Ręcznie",
        'period_auto_success': "Automatycznie wyznaczono okres:", 'period_history_error': "Błąd w pliku historii. Wprowadź daty ręcznie.",
        'period_no_history': "Nie znaleziono historii. Wprowadź pierwszy okres ręcznie.",
        'start_date_label': "Data początkowa", 'end_date_label': "Data końcowa",
        'generate_doc_header': "3. Generuj dokument", 'generate_pdf_button': "🚀 Wygeneruj PDF",
        'spinner_text': "Trwa generowanie dokumentu PDF...", 'doc_success': "Dokument został pomyślnie wygenerowany!",
        'download_button': "📥 Pobierz wygenerowany plik PDF",
        'err_no_signature': "Musisz wgrać plik z podpisem w panelu bocznym.", 'err_no_works': "Musisz dodać przynajmniej jeden utwór.",
        'err_bad_link': "Link do ewidencji jest wymagany i musi być poprawnym adresem URL.", 'err_no_period': "Musisz podać pełny okres rozliczeniowy."
    },
    'en': {
        'page_title': "Report Generator", 'app_title': "📄 Employee's Work Report Generator",
        'settings_header': "⚙️ Settings", 'lang_select_label': "UI Language",
        'signature_header': "✍️ Signature", 'upload_label': "Choose a PNG file with your signature",
        'upload_help': "The uploaded file will be used in the generated document.",
        'signature_success': "Signature has been uploaded and saved!",
        'current_signature': "Currently used signature:", 'delete_signature_button': "🗑️ Delete saved signature",
        'signature_deleted': "Saved signature has been deleted.", 'no_signature_to_delete': "No saved signature to delete.",
        'no_signature': "No uploaded or saved signature.", 'history_header': "🗓️ Period History",
        'last_date_label': "Last saved end date:", 'no_history': "None",
        'overwrite_date_label': "Overwrite date", 'save_history_button': "💾 Save history",
        'history_updated': "History updated!", 'font_warning': "DejaVu fonts not found. Some characters may not render correctly.",
        'add_works_header': "1. Add completed works", 'project_name_label': "Project name",
        'work_desc_label': "Description of work performed", 'add_work_button': "➕ Add work to the list",
        'works_list_header': "**List of added works:**", 'delete_entry_help': "Delete this entry",
        'other_data_header': "2. Provide other data", 'link_label': "Shared link to evidence (e.g., https://...)",
        'period_select_header': "Billing period selection", 'period_auto': "Automatically (recommended)", 'period_manual': "Manually",
        'period_auto_success': "Period automatically determined:", 'period_history_error': "Error in history file. Please enter dates manually.",
        'period_no_history': "No history found. Please enter the first period manually.",
        'start_date_label': "Start date", 'end_date_label': "End date",
        'generate_doc_header': "3. Generate document", 'generate_pdf_button': "🚀 Generate PDF",
        'spinner_text': "Generating PDF document...", 'doc_success': "Document has been successfully generated!",
        'download_button': "📥 Download generated PDF file",
        'err_no_signature': "You must upload a signature file in the sidebar.", 'err_no_works': "You must add at least one work item.",
        'err_bad_link': "The evidence link is required and must be a valid URL.", 'err_no_period': "You must provide a full billing period."
    }
}
def t(key):
    return translations[st.session_state.lang].get(key, key)

#======================================================================
#  LOGIKA BIZNESOWA (BEZ ZMIAN)
#======================================================================
def wczytaj_ostatni_okres():
    try:
        with open(PLIK_HISTORII, 'r') as f:
            dane = json.load(f)
            return dane.get("ostatnia_data_koncowa")
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def zapisz_nowy_okres(data_koncowa_str):
    dane = {"ostatnia_data_koncowa": data_koncowa_str}
    with open(PLIK_HISTORII, 'w') as f:
        json.dump(dane, f, indent=4)

def generuj_pdf(projekty, wspolny_link, start_okresu, koniec_okresu, signature_bytes):
    # This function remains unchanged
    os.makedirs(FOLDER_PDF, exist_ok=True)
    miesiac_i_rok_dzisiejszy = datetime.date.today().strftime("%m_%Y")
    nazwa_pliku_pdf = f"{FOLDER_PDF}/Oświadczenie_Mateusz_Byrtus_{miesiac_i_rok_dzisiejszy}.pdf"
    
    doc = SimpleDocTemplate(nazwa_pliku_pdf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    story = []

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(name='Normal', fontName=FONT_NAME, fontSize=8, leading=10)
    style_lp = ParagraphStyle(name='LpStyle', parent=style_normal, alignment=TA_CENTER)
    style_title = ParagraphStyle(name='Title', fontName=FONT_BOLD, fontSize=10, alignment=TA_CENTER, spaceAfter=1*cm)
    style_header = ParagraphStyle(name='Header', fontName=FONT_BOLD, fontSize=8, alignment=TA_CENTER)
    style_signature_desc = ParagraphStyle(name='SignatureDesc', fontName=FONT_BOLD, fontSize=8, alignment=TA_LEFT)
    style_helper = ParagraphStyle(name='Helper', fontName=FONT_NAME, fontSize=5, leading=7, textColor=colors.grey)
    style_justify = ParagraphStyle(name='Justify', parent=style_normal, alignment=TA_JUSTIFY)

    story.append(Paragraph("Oświadczenie Pracownika raportującego utwory powstałe w danym okresie rozliczeniowym", style_title))
    story.append(Paragraph("Przesyłam zgłoszenie dotyczące wykonania przeze mnie utworów chronionych prawami autorskimi.", style_normal))
    story.append(Spacer(1, 0.5*cm))

    naglowki = [Paragraph(h, style_header) for h in ["L.p.", "Nazwa projektu, w ramach którego został wytworzony utwór", "Wytworzony utwór", "Ewidencja i archiwizacja utworu"]]
    pomocnicze = [
        Paragraph("[numer projektu w tabeli]", style_helper),
        Paragraph("[nazwa projektu, w ramach którego powstał utwór – według nomenklatury firmowej]", style_helper),
        Paragraph("[nazwa robocza określająca rodzaj rezultatu prac, np. projekt grafiku, animacji itd.)", style_helper),
        Paragraph("[link do repozytorium, gdzie oryginalny utwór został w trwały sposób zaewidencjonowany]", style_helper)
    ]
    dane_tabeli = [naglowki, pomocnicze]
    link_paragraph = Paragraph(f'<a href="{wspolny_link}" color="blue">{miesiac_i_rok_dzisiejszy}</a>', style_normal) if wspolny_link else ''
    for i, p in enumerate(projekty):
        dane_tabeli.append([Paragraph(str(i + 1), style_lp), Paragraph(p["nazwa"], style_normal), Paragraph(p["opis"], style_normal), link_paragraph])
    for i in range(len(projekty) + 1, 10):
        dane_tabeli.append([Paragraph(str(i), style_lp), '', '', ''])
    
    tabela = Table(dane_tabeli, colWidths=[1.5*cm, 5*cm, 6*cm, 3*cm])
    tabela.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('GRID', (0,0), (-1,-1), 1, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(tabela)
    story.append(Spacer(1, 1*cm))

    tekst_prawny1 = "Przez wskazanie rezultatów pracy twórczej w niniejszym oświadczeniu niniejszym potwierdzam, że są to utwory stanowiące przejaw mojej działalności twórczej o indywidualnym charakterze, a tym samym chronione prawami ustawy z dnia 4 lutego 1994 r. o prawie autorskim i prawach pokrewnych (Dz.U. z 2022 r. poz. 2509, t.j.)."
    story.append(Paragraph(tekst_prawny1, style_justify))
    story.append(Spacer(1, 0.5*cm))
    okres_rozliczeniowy_str = f"{start_okresu} - {koniec_okresu}"
    tekst_prawny2 = f"Oświadczam, że wskazane rezultaty pracy twórczej zostały wykonane w terminie aktualnego okresu rozliczeniowego dla utworów chronionych prawami autorskimi, tj. w terminie {okres_rozliczeniowy_str}"
    story.append(Paragraph(tekst_prawny2, style_justify))
    story.append(Spacer(1, 2*cm))

    data_dzisiejsza = datetime.date.today().strftime("%d.%m.%Y")
    try:
        podpis_img = Image(io.BytesIO(signature_bytes), width=4*cm, height=1.5*cm)
    except Exception as e:
        return None, f"Błąd przetwarzania obrazu podpisu: {e}"
    
    dane_podpisu = [[Paragraph(data_dzisiejsza, style_normal), podpis_img, ''], [Paragraph("data i podpis Pracownika", style_signature_desc), '', '']]
    tabela_podpisu = Table(dane_podpisu, colWidths=[2.5*cm, 5*cm, 7.5*cm])
    tabela_podpisu.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('ALIGN', (0,0), (0,0), 'LEFT'), ('ALIGN', (1,0), (1,0), 'LEFT'), ('SPAN', (0, 1), (1, 1))]))
    story.append(tabela_podpisu)

    doc.build(story)
    return nazwa_pliku_pdf, None

#======================================================================
#  INTERFEJS GRAFICZNY STREAMLIT
#======================================================================

# --- Inicjalizacja stanu sesji ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'pl'
if 'projekty' not in st.session_state:
    st.session_state.projekty = []
if 'signature_data' not in st.session_state:
    try:
        with open(PLIK_PODPISU_ZAPISANEGO, "rb") as f:
            st.session_state.signature_data = f.read()
    except FileNotFoundError:
        st.session_state.signature_data = None

# --- Panel boczny (Sidebar) ---
with st.sidebar:
    st.header(t('settings_header'))
    
    # KOREKTA: Użycie "State Check and Rerun" pattern
    # Użycie dwujęzycznej etykiety, aby była zawsze zrozumiała
    selected_lang = st.selectbox(
        label="UI Language / Język interfejsu", 
        options=['pl', 'en'], 
        index=0 if st.session_state.lang == 'pl' else 1, # Ustawia domyślną pozycję na podstawie stanu
        format_func=lambda lang: "Polski" if lang == 'pl' else "English"
    )
    # Jeśli wartość widgetu różni się od stanu, zaktualizuj stan i wymuś pełne odświeżenie
    if selected_lang != st.session_state.lang:
        st.session_state.lang = selected_lang
        st.rerun()

    st.divider()

    st.subheader(t('signature_header'))
    uploaded_file = st.file_uploader(t('upload_label'), type=['png'], help=t('upload_help'))
    if uploaded_file:
        st.session_state.signature_data = uploaded_file.getvalue()
        with open(PLIK_PODPISU_ZAPISANEGO, "wb") as f: f.write(st.session_state.signature_data)
        st.success(t('signature_success'))
    if st.session_state.signature_data:
        st.write(t('current_signature'))
        st.image(st.session_state.signature_data, width=150)
        if st.button(t('delete_signature_button'), type="secondary"):
            st.session_state.signature_data = None
            try:
                os.remove(PLIK_PODPISU_ZAPISANEGO)
                st.success(t('signature_deleted'))
            except FileNotFoundError:
                st.info(t('no_signature_to_delete'))
            time.sleep(1); st.rerun()
    else:
        st.info(t('no_signature'))

    st.divider()
    
    st.subheader(t('history_header'))
    aktualna_ostatnia_data_str = wczytaj_ostatni_okres()
    default_date = datetime.datetime.strptime(aktualna_ostatnia_data_str, "%d.%m.%Y").date() if aktualna_ostatnia_data_str else None
    with st.form("form_modyfikacji_daty"):
        st.write(t('last_date_label'))
        st.info(aktualna_ostatnia_data_str or t('no_history'))
        nowa_data_do_zapisu = st.date_input(t('overwrite_date_label'), value=default_date, format="DD.MM.YYYY")
        if st.form_submit_button(t('save_history_button')) and nowa_data_do_zapisu:
            zapisz_nowy_okres(nowa_data_do_zapisu.strftime("%d.%m.%Y"))
            st.success(t('history_updated')); time.sleep(1); st.rerun()

    if FONT_NAME == 'Helvetica':
        st.warning(t('font_warning'))

# --- Główna część aplikacji ---
st.set_page_config(layout="centered", page_title=t('page_title')) # To jest tutaj, ale sidebar renderuje się pierwszy
st.title(t('app_title'))

st.header(t('add_works_header'))
with st.form("formularz_utworu", clear_on_submit=True):
    nowa_nazwa = st.text_input(t('project_name_label'))
    nowy_opis = st.text_input(t('work_desc_label'))
    if st.form_submit_button(t('add_work_button')) and nowa_nazwa:
        st.session_state.projekty.append({"nazwa": nowa_nazwa, "opis": nowy_opis})

if st.session_state.projekty:
    st.write(t('works_list_header'))
    for i, projekt in enumerate(st.session_state.projekty):
        cols = st.columns([1, 8, 1])
        cols[0].write(f"{i+1}.")
        cols[1].info(f"**{projekt['nazwa']}**: {projekt['opis']}")
        if cols[2].button("❌", key=f"usun_{i}", help=t('delete_entry_help')):
            st.session_state.projekty.pop(i); st.rerun()

st.header(t('other_data_header'))
wspolny_link = st.text_input(t('link_label'), key="link_input")
wybor_okresu = st.radio(t('period_select_header'), (t('period_auto'), t('period_manual')), horizontal=True)

start_okresu, koniec_okresu = "", ""
if wybor_okresu == t('period_auto'):
    ostatnia_data_str = wczytaj_ostatni_okres()
    if ostatnia_data_str:
        try:
            ostatnia_data_obj = datetime.datetime.strptime(ostatnia_data_str, "%d.%m.%Y").date()
            start_date_obj, end_date_obj = ostatnia_data_obj + datetime.timedelta(days=1), ostatnia_data_obj + datetime.timedelta(days=30)
            start_okresu, koniec_okresu = start_date_obj.strftime("%d.%m.%Y"), end_date_obj.strftime("%d.%m.%Y")
            st.success(f"{t('period_auto_success')} **{start_okresu} - {koniec_okresu}**")
        except ValueError:
            st.error(t('period_history_error')); wybor_okresu = t('period_manual')
    else:
        st.info(t('period_no_history')); wybor_okresu = t('period_manual')
if wybor_okresu == t('period_manual'):
    col1, col2 = st.columns(2)
    start_date_obj = col1.date_input(t('start_date_label'), value=None, format="DD.MM.YYYY")
    end_date_obj = col2.date_input(t('end_date_label'), value=None, format="DD.MM.YYYY")
    start_okresu = start_date_obj.strftime("%d.%m.%Y") if start_date_obj else ""
    koniec_okresu = end_date_obj.strftime("%d.%m.%Y") if end_date_obj else ""

st.header(t('generate_doc_header'))

if st.button(t('generate_pdf_button')):
    errors = []
    if not st.session_state.signature_data: errors.append(t('err_no_signature'))
    if not st.session_state.projekty: errors.append(t('err_no_works'))
    if not wspolny_link or not URL_REGEX.match(wspolny_link): errors.append(t('err_bad_link'))
    if not start_okresu or not koniec_okresu: errors.append(t('err_no_period'))
    
    if errors:
        for error in errors: st.error(error)
    else:
        with st.spinner(t('spinner_text')):
            nazwa_pliku, blad_generowania = generuj_pdf(st.session_state.projekty, wspolny_link, start_okresu, koniec_okresu, st.session_state.signature_data)
        if not blad_generowania:
            st.success(t('doc_success'))
            zapisz_nowy_okres(koniec_okresu)
            with open(nazwa_pliku, "rb") as file:
                st.download_button(label=t('download_button'), data=file, file_name=os.path.basename(nazwa_pliku), mime="application/pdf")
        else:
            st.error(blad_generowania)