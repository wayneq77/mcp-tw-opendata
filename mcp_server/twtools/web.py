"""網頁/PDF 工具 (4 tools)"""
import requests

def fetch_url_as_markdown(url: str, include_links: bool = True, include_images: bool = False) -> dict:
    """抓取網頁主內容並轉成 Markdown"""
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {"url": url, "error": "無法下載頁面"}
        result = trafilatura.extract(downloaded, include_links=include_links,
                                      include_images=include_images, output_format="txt")
        if not result:
            return {"url": url, "error": "無法抽取主要內容（可能是列表型頁面）"}
        return {"url": url, "content": result, "length": len(result)}
    except ImportError:
        return {"error": "需要 trafilatura 套件"}
    except Exception as e:
        return {"url": url, "error": str(e)}

def extract_pdf_text(url: str) -> dict:
    """提取 PDF 全文"""
    try:
        import fitz  # PyMuPDF
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        doc = fitz.open(stream=resp.content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return {"url": url, "pages": len(doc), "text": text[:50000], "truncated": len(text) > 50000}
    except ImportError:
        return {"error": "需要 PyMuPDF 套件"}
    except Exception as e:
        return {"url": url, "error": str(e)}

def extract_pdf_pages(url: str, pages: str = "1") -> dict:
    """提取 PDF 指定頁碼"""
    try:
        import fitz
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        doc = fitz.open(stream=resp.content, filetype="pdf")
        # Parse page spec like "1,3,5-7"
        page_nums = set()
        for part in pages.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                for i in range(int(a), int(b) + 1):
                    page_nums.add(i)
            else:
                page_nums.add(int(part))
        results = []
        for pn in sorted(page_nums):
            if 1 <= pn <= len(doc):
                results.append({"page": pn, "text": doc[pn - 1].get_text()})
        return {"url": url, "total_pages": len(doc), "extracted": results}
    except ImportError:
        return {"error": "需要 PyMuPDF 套件"}
    except Exception as e:
        return {"url": url, "error": str(e)}

def extract_pdf_metadata(url: str) -> dict:
    """提取 PDF 元資料"""
    try:
        import fitz
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        doc = fitz.open(stream=resp.content, filetype="pdf")
        meta = doc.metadata
        return {"url": url, "pages": len(doc), "metadata": meta}
    except ImportError:
        return {"error": "需要 PyMuPDF 套件"}
    except Exception as e:
        return {"url": url, "error": str(e)}
