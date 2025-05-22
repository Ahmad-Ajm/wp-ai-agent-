
def _process_deepseek(self, prompt):
    headers = {'Authorization': f'Bearer {self.api_key}'}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(
        'https://api.deepseek.com/v1/chat/completions',
        headers=headers,
        json=data
    )
    resp_json = response.json()

    if isinstance(resp_json, dict) and 'error' in resp_json:
        msg = resp_json['error'].get('message', 'Unknown DeepSeek Error')
        raise Exception(f"DeepSeek Error: {msg}")

    choices = resp_json.get('choices')
    if not isinstance(choices, list) or len(choices) == 0:
        raise Exception("رد غير متوقع من DeepSeek: لا توجد خيارات متاحة")

    choice = choices[0]
    message = choice.get('message')
    if not isinstance(message, dict) or 'content' not in message:
        raise Exception("الرد غير مكتمل من DeepSeek")

    return message['content']
