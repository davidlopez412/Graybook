import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, '../3_Outputs')));

const MONTHS = [
  'January','February','March','April','May','June',
  'July','August','September','October','November','December',
];

function fmtDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return `${String(d).padStart(2, '0')} ${MONTHS[m - 1]} ${y}`;
}

const SYSTEM_PROMPT = `You are a naval historian of the Pacific War (1941–1942), writing for a serious, well-read audience already familiar with the campaign. Your tone is authoritative, precise, and unsentimental.

Write an interpretation of the CINCPAC Graybook entry in exactly three short paragraphs (2–4 sentences each):
1. knew — what the fleet commander knew on this date, given this entry.
2. didntKnow — what he did NOT yet know: consequences, enemy intentions, or facts hidden from him at the time.
3. coming — what was about to happen as a result, looking just ahead from this date.

Where appropriate, refer to the commander by surname or as "he" — do not attribute the entry to a different admiral than the one named in the OFFICER field.

Do not merely restate the entry; add the historian's perspective. Do not use the second person. No preamble or closing remarks.

Return ONLY valid JSON, no markdown fences, in exactly this shape:
{"knew":"...","didntKnow":"...","coming":"..."}`;

function buildUserMessage({ date, place, command, actual }) {
  const lines = [
    `DATE: ${fmtDate(date)}`,
    `OFFICER: ${command}`,
  ];
  if (place) lines.push(`LOCATION: ${place}`);
  lines.push('ENTRY:');
  lines.push(`"""${Array.isArray(actual) ? actual.join('\n') : String(actual)}"""`);
  return lines.join('\n');
}

app.post('/api/historian', async (req, res) => {
  const { date, place, command, actual } = req.body;
  if (!date || !command || !actual) {
    return res.status(400).json({ error: 'Missing required fields: date, command, actual' });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'ANTHROPIC_API_KEY not set' });
  }

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-opus-4-8',
        max_tokens: 1024,
        system: SYSTEM_PROMPT,
        messages: [{ role: 'user', content: buildUserMessage({ date, place, command, actual }) }],
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      return res.status(500).json({ error: `Anthropic API error: ${errText}` });
    }

    const data = await response.json();
    const content = data.content?.[0]?.text ?? '';
    res.json({ content });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Listening on http://localhost:${PORT}`));
