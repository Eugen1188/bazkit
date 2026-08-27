import {
  CommonModule
} from '@angular/common';

import {
  Component,
  OnInit
} from '@angular/core';

import {
  FormsModule
} from '@angular/forms';

import {
  ActivatedRoute,
  Router
} from '@angular/router';

import {
  CommunityComment,
  CommunityPost
} from '../../models/community.model';

import {
  CommunityService
} from '../../services/community.service';


@Component({
  selector:
    'app-community-detail',

  standalone:
    true,

  imports: [
    CommonModule,
    FormsModule
  ],

  templateUrl:
    './community-detail.component.html',

  styleUrl:
    './community-detail.component.scss'
})
export class CommunityDetailComponent
implements OnInit {

  post:
    CommunityPost | null =
      null;


  comments:
    CommunityComment[] =
      [];


  commentText =
    '';


  isLoading =
    true;


  isSubmittingComment =
    false;


  isCopying =
    false;

  isEditing = false;
  isSavingPost = false;
  isDeletingPost = false;
  editTitle = '';
  editContent = '';
  editThreadCategory = 'other';


  message =
    '';


  errorMessage =
    '';


  stars = [
    1,
    2,
    3,
    4,
    5
  ];


  constructor(
    private route:
      ActivatedRoute,

    private router:
      Router,

    private communityService:
      CommunityService
  ) {}


  ngOnInit():
    void {

    const id =
      Number(
        this.route.snapshot
          .paramMap
          .get(
            'id'
          )
      );


    if (
      !id
    ) {

      this.router.navigate([
        '/main/community'
      ]);

      return;
    }


    this.loadPost(
      id
    );

    this.loadComments(
      id
    );
  }


  loadPost(
    id:
      number
  ): void {

    this.isLoading =
      true;

    this.errorMessage =
      '';


    this.communityService
      .getPost(
        id
      )
      .subscribe({

        next:
          post => {

            this.post =
              post;

            this.isLoading =
              false;
          },


        error:
          error => {

            console.error(
              'Community-Beitrag konnte nicht geladen werden:',
              error
            );

            this.isLoading =
              false;

            this.errorMessage =
              'Der Beitrag konnte nicht geladen werden.';
          }

      });
  }


  loadComments(
    id:
      number
  ): void {

    this.communityService
      .getComments(
        id
      )
      .subscribe({

        next:
          comments => {

            this.comments =
              comments;
          },


        error:
          error => {

            console.error(
              'Kommentare konnten nicht geladen werden:',
              error
            );
          }

      });
  }


  goBack():
    void {

    this.router.navigate([
      '/main/community'
    ]);
  }


  toggleLike():
    void {

    if (
      !this.post
    ) {

      return;
    }


    this.communityService
      .toggleLike(
        this.post.id
      )
      .subscribe({

        next:
          response => {

            if (
              !this.post
            ) {

              return;
            }


            this.post.liked_by_me =
              response.liked;

            this.post.like_count =
              response.like_count;
          },


        error:
          error => {

            console.error(
              'Like konnte nicht gespeichert werden:',
              error
            );
          }

      });
  }


  rate(
    value:
      number
  ): void {

    if (
      !this.post
      ||
      this.post.post_type ===
        'thread'
    ) {

      return;
    }


    this.communityService
      .ratePost(
        this.post.id,
        value
      )
      .subscribe({

        next:
          response => {

            if (
              !this.post
            ) {

              return;
            }


            this.post.my_rating =
              response.rating;

            this.post.rating_average =
              response.rating_average;

            this.post.rating_count =
              response.rating_count;
          },


        error:
          error => {

            console.error(
              'Bewertung konnte nicht gespeichert werden:',
              error
            );
          }

      });
  }


  submitComment():
    void {

    if (
      !this.post
    ) {

      return;
    }


    const content =
      this.commentText
        .trim();


    if (
      !content
    ) {

      return;
    }


    this.isSubmittingComment =
      true;


    this.communityService
      .createComment(
        this.post.id,
        content
      )
      .subscribe({

        next:
          comment => {

            this.comments.push(
              comment
            );

            this.commentText =
              '';

            this.isSubmittingComment =
              false;


            if (
              this.post
            ) {

              this.post.comment_count =
                this.comments.length;
            }
          },


        error:
          error => {

            console.error(
              'Kommentar konnte nicht erstellt werden:',
              error
            );

            this.isSubmittingComment =
              false;
          }

      });
  }


  copyToMyAccount():
    void {

    if (
      !this.post
      ||
      this.post.post_type ===
        'thread'
    ) {

      return;
    }


    this.isCopying =
      true;

    this.message =
      '';


    this.communityService
      .copyPost(
        this.post.id
      )
      .subscribe({

        next:
          response => {

            this.isCopying =
              false;

            this.message =
              response.detail;
          },


        error:
          error => {

            console.error(
              'Übernahme fehlgeschlagen:',
              error
            );

            this.isCopying =
              false;

            this.message =
              'Der Inhalt konnte nicht übernommen werden.';
          }

      });
  }

  editPost(): void {
    if (!this.post || !this.post.is_author) return;
    if (this.post.post_type === 'recipe' && this.post.recipe) {
      void this.router.navigate(
        ['/main/recipe-list', this.post.recipe.id, 'edit'],
        { queryParams: { communityPost: this.post.id } }
      );
      return;
    }
    if (this.post.post_type === 'list' && this.post.saved_list) {
      void this.router.navigate(
        ['/main/saved-list', this.post.saved_list.id, 'edit'],
        { queryParams: { communityPost: this.post.id } }
      );
      return;
    }
    this.editTitle = this.post.title;
    this.editContent = this.post.content;
    this.editThreadCategory = this.post.thread_category || 'other';
    this.isEditing = true;
  }

  cancelEdit(): void {
    if (!this.isSavingPost) this.isEditing = false;
  }

  savePost(): void {
    if (!this.post || !this.editTitle.trim() || !this.editContent.trim()) return;
    this.isSavingPost = true;
    this.communityService.updatePost(this.post.id, {
      title: this.editTitle.trim(),
      content: this.editContent.trim(),
      thread_category: this.editThreadCategory
    }).subscribe({
      next: post => {
        this.post = post;
        this.isSavingPost = false;
        this.isEditing = false;
        this.message = 'Der Beitrag wurde aktualisiert.';
      },
      error: error => {
        console.error('Beitrag konnte nicht aktualisiert werden:', error);
        this.isSavingPost = false;
        this.errorMessage = 'Der Beitrag konnte nicht aktualisiert werden.';
      }
    });
  }

  deletePost(): void {
    if (!this.post || !this.post.is_author || this.isDeletingPost) return;
    if (!confirm(`Möchtest du den Community-Beitrag „${this.post.display_title}“ wirklich löschen?`)) return;
    this.isDeletingPost = true;
    this.communityService.deletePost(this.post.id).subscribe({
      next: () => void this.router.navigate(['/main/community']),
      error: error => {
        console.error('Beitrag konnte nicht gelöscht werden:', error);
        this.isDeletingPost = false;
        this.errorMessage = 'Der Beitrag konnte nicht gelöscht werden.';
      }
    });
  }

}
