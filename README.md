# NFDIxCS Scientific Text Extraction Technology Demo

This repository contains the code for the NFDIxCS scientific text extraction technology demo.

To run the app locally, a working Docker environment is required.  
You also need to replace `<GEMINI-API-KEY>` with your own API key.

```
docker run -d --name gradio-app --restart unless-stopped -p 127.0.0.1:7863:7860 -e API_KEY=<GEMINI-API-KEY> gradio-app
```

After running this command, the app should be accessible at [http://localhost:7863](http://localhost:7863).

**Important Notice:** Due to licensing constraints, the few-shot examples are not included in this repository. If this feature is required, you must add them to `/app/Filtered_Few-Shot_Examples_Final_fulltext.xlsx`.

## License

This work is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
