from openai import OpenAI

client = OpenAI()

def ask_chat_gpt(prompt):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "You are an expert programmer and teaching python to elementary school students."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
    )

    return completion.choices[0].message.content


if __name__ == '__main__':
    prompt = "pythonとは何か簡潔に教えて"
    response = ask_chat_gpt(prompt)
    print(response)
