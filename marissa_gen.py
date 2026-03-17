import json
import asyncio
from agents import OracleBrain
from prompts import HTML_TEMPLATE_START, HTML_TEMPLATE_END
import os

api_keys = ["AIzaSyD0Y9VtsUXn80FHepCasgoFi6KbQ6XIvrc"]
try:
    with open("app_settings.json", "r") as f:
         data = json.load(f)
         api_keys = data.get("api_keys", api_keys)
except:
    pass

brain = OracleBrain(api_keys=api_keys)

order_note = """
Marissa Angelique 11/11
Eamon Mitchell 12/30

Moira his Scorpio mom

I need to spy on their marriage again I know there is so much more to uncover

Eamon's father only went out to Tennessee a year ago. He has not been there years correction.

I want to uncover their marriage more. I know there is so much more I need to see. Thank you for being my visionary.😉
Message:Yes, stuff happened when he was 12 but I don't know all of it other than that vision you gave me

There was something else we discussed me and him, and I will give you those visuals. When we trauma bonded during Anastasia and I told him about my abusive father who I have no contact with, and how my mom, my brother, and I survived that he was very loving and tender and empathetic. Moira may or may not be aware of what I have survived. I don't know how much or how little Eamon has told her of me. But I'm sure she's spied my Instagram.

That was when he told me that something happened when he was a kid, but he wasn't ready to tell me through our audios or wanted to, but was at his mom's law, firm and busy working.

Then the time that we spent by the ghost light on the stage alone in the theater And trauma bonded again he told me it's so weird how our parents were our ages when they got married and had us and how they tried to emulate the characters on "Friends" TV show or "Melrose Place" And how both of our moms dressed so similar and elegant with the red lipstick and the Carolyn Bessette fashion. We even joked that they could be friends because of how much we have in common
Message:But we believed in that moment and what we said was, they were too immature to have started having kids and how we couldn't have a imagined having kids at our ages because we still feel like kids ourselves. My parents were certainly very immature. He did not say whether or not with his parents, but we both said how weird it was to be children and watch their dynamics.

Then I joked with him and said did you ever "catch them" and he laughed and said yes, and it sounded like it had been a few times. I had found a sex tape my parents had made with my beautiful mom giving my dad a hand job when I was 10 and how traumatizing it was. Thankfully, I only watched a few minutes before turning it off.

My dad had a disgusting porn addiction and would sometimes make family home videos on his camera and with film my mom's butt

Eamon sensed my trauma and put his arms on me to comfort me. He told me his parents were always affectionate and seemingly lovey-dovey but it also seemed like he wanted to tell me more, but was hiding it out of perhaps shame or embarrassment, but he did tell me something
Marissa
Message:He told me as a little boy he was once again up at night and walked down that dimly lit hall because he heard Moira making "moaning sounds" so he thought something was wrong and when he peered by his parents large door to their large bedroom suite he saw his dad on top of her and watched as she propped herself on top of him in absolute zeal and they were breathing heavily. Then he stopped and I felt terrible because how the heck do you process that as a kid but then my parents were no better at least his parents seemed in love.

We need to dive into this sexual stuff too, even if it's uncomfortable because there is something here

Eamon also told me that the relationship started with The was purely sex at first and then it seems like she manipulated him to commit. They never dated. It was all built off sex initially no emotional connection
10:48 AM
4:09 PM
Message:Hi Nes I'm sorry for the delay. I am in California and on the Pacific time
Message:Of course I can leave a review. No worries at all and thank you so much.
Marissa
Message:I love our sessions together. I really appreciate it!!
7:28 PM
Marissa
Message:Had another vision of me being sick and him taking care of me seemingly worried and so attentive and loving. We were living in LA which is my happy place given the relationships I built during my contract with Oklahoma the musical
8:22 PM
Date:
Sun, Mar 87:09pm EST

Message:I love what I said in my audio. In the first one I made a joke about ballet class, and the pianist I knew he would laugh. I think this was enough and trust me. I did not smother him. I spoke slowly so that's probably why it seems long but I like what I said.
Message:See, I did not rescue him
Message:I also told him how that dancer is still in him and that I know he's still there
Message:Also, just so we're clear Eamon already knows about my ex. I told him this during Anastasia. He already knows so this wasn't new information but he did not know that I had gone to North Carolina.
Marissa
Message:Oh wow he said I was right. I think it really hit his heart in a good way.
3:23 AM
Message:OK, I deleted that one and I re-recorded and this one is much better

Message:I then ended with and told him that dancer and that Ballet rebel he told me he was still in him and that he's still there.

I promise I made it short and sweet very queen of cups, but without being over the top
Marissa
Message:It seems to have landed good with him. I think I definitely pulled at his heart. He did not feel I was telling him what to do at all and I think he realizes that I'm right and solidifying that two of cups between us that always comes out in the tarot.
4:27 AM
Marissa
Message:I think this was a lightbulb moment for him. I stayed the lighthouse
5:33 AM
Message:Hi Nes. No rush of course but I'm wondering if I'll receive my reading tonight?
Marissa
Message:I'm buying another one now about entering his mind.
"""

reading_topic = "Family Secrets Psychic Reading | Reveal Generational Trauma and Hidden Truths | Deep Ancestral Scan | Heal Family Blockages"
client_email = "marissaangeliquegj@gmail.com"

def cb(msg):
    print(msg)

draft, delivery, usage, audio = brain.run_cycle(
    order_note=order_note,
    reading_topic=reading_topic,
    client_email=client_email,
    target_length="13000",
    generate_audio=False,
    progress_callback=cb
)

from google.generativeai.types import HarmCategory, HarmBlockThreshold
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

if "<!DOCTYPE html>" not in draft:
    final_content = draft.replace("```html", "").replace("```", "")
    full_html = HTML_TEMPLATE_START + final_content + HTML_TEMPLATE_END
else:
    full_html = draft.replace("```html", "").replace("```", "")

# Instead of asking gemini here (since it was blocking), use standard text appending


with open("marissa_html.html", "w", encoding="utf-8") as f:
    f.write(full_html)

print("Saved HTML to marissa_html.html")
