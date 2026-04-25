export const initialMessages = [
  {
    role: "user",
    content: "When should I apply for OPT?"
  },
  {
    role: "assistant",
    content:
      "You may apply for post-completion OPT up to 90 days before your program end date and up to 60 days after.",
    citations: [
      {
        title: "doc 1",
        chunk_text:
          "Students may apply for post-completion OPT up to 90 days before the program end date and no later than 60 days after the program end date.",
        doc_id: "uscis_opt_timeline",
        chunk_id: 101,
        rank: 1
      },
      {
        title: "doc 2",
        chunk_text:
          "Students should work with their DSO to request OPT recommendation in SEVIS before filing with USCIS.",
        doc_id: "international_student_office_opt_guide",
        chunk_id: 205,
        rank: 2
      }
    ]
  },
  {
    role: "user",
    content: "Can I work while waiting for approval?"
  },
  {
    role: "assistant",
    content:
      "No. You should not begin working until your OPT is approved, your EAD card has been issued, and the authorized start date has arrived.",
    citations: [
      {
        title: "doc 1",
        chunk_text:
          "Employment may begin only after authorization is approved and the valid employment authorization period has started.",
        doc_id: "f1_employment_rules",
        chunk_id: 312,
        rank: 1
      }
    ]
  }
];