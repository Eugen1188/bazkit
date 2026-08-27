export type CommunityPostType =
  'recipe'
  | 'list'
  | 'thread';


export interface CommunityAuthor {
  id: number;

  name: string;
}


export interface CommunityIngredient {
  id: number;

  name: string;

  quantity:
    number | null;

  unit: string;
}


export interface CommunityRecipe {
  id: number;

  name: string;

  description: string;

  servings: number;

  preparation_time:
    number | null;

  category: string;

  instructions: string;

  notes: string;

  calories: number | string | null;

  protein: number | string | null;

  carbohydrates: number | string | null;

  fat: number | string | null;

  fiber: number | string | null;

  estimated_price: number | string | null;

  ingredients:
    CommunityIngredient[];

  created_at: string;
}


export interface CommunitySavedListItem {
  id: number;

  name: string;

  quantity:
    number | null;

  unit: string;

  note: string;
}


export interface CommunitySavedList {
  id: number;

  title: string;

  created_at: string;

  item_count: number;

  items:
    CommunitySavedListItem[];
}


export interface CommunityPost {
  id: number;

  post_type:
    CommunityPostType;

  author:
    CommunityAuthor;

  title: string;

  content: string;

  thread_category: string;

  recipe:
    CommunityRecipe | null;

  saved_list:
    CommunitySavedList | null;

  display_title: string;

  display_description: string;

  comment_count: number;

  like_count: number;

  liked_by_me: boolean;

  rating_average:
    number | null;

  rating_count: number;

  my_rating:
    number | null;

  is_author: boolean;

  created_at: string;

  updated_at: string;
}


export interface CommunityComment {
  id: number;

  author:
    CommunityAuthor;

  content: string;

  created_at: string;

  updated_at: string;
}


export interface CommunityRecipeOption {
  id: number;

  name: string;
}


export interface CommunitySavedListOption {
  id: number;

  title: string;
}


export interface CommunityShareOptions {
  recipes:
    CommunityRecipeOption[];

  saved_lists:
    CommunitySavedListOption[];
}


export interface CreateCommunityPostPayload {
  post_type:
    CommunityPostType;

  recipe_id?:
    number;

  saved_list_id?:
    number;

  title?:
    string;

  content?:
    string;

  thread_category?:
    string;
}


export interface CommunityLikeResponse {
  liked: boolean;

  like_count: number;
}


export interface CommunityRatingResponse {
  rating: number;

  rating_average: number;

  rating_count: number;
}


export interface CommunityCopyResponse {
  type:
    'recipe'
    | 'list';

  id: number;

  detail: string;
}

export interface UpdateCommunityPostPayload {
  title?: string;
  content?: string;
  thread_category?: string;
}
